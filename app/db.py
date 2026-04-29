"""
数据库模块：连接 TeslaMate PostgreSQL，读取 drives 表数据
"""
import logging
from typing import Optional
import json
import psycopg2
import psycopg2.extras
from app.config import config

logger = logging.getLogger(__name__)

def get_connection():
    """建立并返回 PostgreSQL 连接"""
    return psycopg2.connect(
        host=config.DB_HOST,
        port=config.DB_PORT,
        dbname=config.DB_NAME,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
    )

def get_address_by_location(latitude: float, longitude: float) -> Optional[str]:
    """根据经纬度查询地址"""
    sql = """
        WITH distance_calc AS (
            SELECT
                id,
                name,
                road,
                neighbourhood,
                city,
                county,
                state,
                raw,
                6371000 * ACOS(
                    COS(RADIANS(%s)) * COS(RADIANS(latitude)) *
                    COS(RADIANS(longitude) - RADIANS(%s))
                    + SIN(RADIANS(%s)) * SIN(RADIANS(latitude))
                ) AS distance
            FROM addresses
            WHERE latitude BETWEEN %s - 0.00045 AND %s + 0.00045
            AND longitude BETWEEN %s - 0.0005 AND %s + 0.0005
        )
        SELECT
            id,
            name,
            road,
            neighbourhood AS township,
            city,
            county AS district,
            state AS province,
            (raw::text LIKE '%%OpenStreetMap%%') AS is_openstreetmap,
            distance
        FROM distance_calc
        WHERE distance <= 50
        ORDER BY is_openstreetmap ASC, distance ASC;
        """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (latitude, longitude, latitude, latitude, latitude, longitude, longitude,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("查询地址失败: %s", e)
        return None

def get_address_by_id(address_id: int) -> Optional[dict]:
    """根据地址 id 查询地址信息"""
    sql = """
        SELECT
            id,
            name,
            road,
            neighbourhood AS township,
            city,
            county AS district,
            state AS province,
            (raw::text LIKE '%%OpenStreetMap%%') AS is_openstreetmap
        FROM addresses
        WHERE id = %s
        """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (address_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("查询地址 id=%s 失败: %s", address_id, e)
        return None

def insert_address(data: dict) -> Optional[int]:
    """将地址信息插入数据库，返回新地址的 id"""
    sql = """
        INSERT INTO addresses (display_name, latitude, longitude, name, road, neighbourhood, city, county, state, raw, inserted_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        RETURNING id
        """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (
                    data.get('display_name'),
                    data.get('latitude'),
                    data.get('longitude'),
                    data.get('name'),
                    data.get('road'),
                    data.get('township'),
                    data.get('city'),
                    data.get('district'),
                    data.get('province'),
                    json.dumps(data.get('raw')),
                ))
                new_id = cur.fetchone()[0]
                conn.commit()
                return new_id
    except psycopg2.Error as e:
        logger.error("插入地址失败: %s", e)
        return None
    
def update_drive_address_id(drive_id: int, start_address_id: int, end_address_id: int) -> bool:
    """更新行程的地址 id"""
    sql = """
        UPDATE drives
        SET start_address_id = %s, end_address_id = %s
        WHERE id = %s
        """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (start_address_id, end_address_id, drive_id,))
                conn.commit()
                return True
    except psycopg2.Error as e:
        logger.error("更新 drive id=%s 地址 id 失败: %s", drive_id, e)
        return False

def get_latest_drive_id(car_id: int) -> Optional[int]:
    """
    查询 drives 表中当前最大的 id。
    如果表为空，返回 None。
    """
    sql = "SELECT MAX(id) FROM drives WHERE car_id = %s AND end_date IS NOT NULL;"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (car_id,))
                row = cur.fetchone()
                return row[0]
    except psycopg2.Error as e:
        logger.error("查询 drives 最大 id 失败: %s", e)
        return None

def get_drive_by_id(car_id: int, drive_id: int) -> Optional[dict]:
    """
    根据 id 查询单条行程记录，返回字典（字段名 → 值）。
    查询不到时返回 None。
    """
    sql = """
        SELECT
            d.id,
            d.start_date,
            TO_CHAR(timezone(%s, d.start_date AT TIME ZONE 'UTC'), 'HH24:MI') AS start_date_str,
            d.end_date,
            d.duration_min,
            d.distance,
            sp.battery_level AS start_battery_level,
            ep.battery_level AS end_battery_level,
            sp.latitude AS start_latitude,
            sp.longitude AS start_longitude,
            ep.latitude AS end_latitude,
            ep.longitude AS end_longitude,
            d.start_address_id,
            d.end_address_id,
            sg.name AS start_geofence_name,
            eg.name AS end_geofence_name,
            CASE 
                WHEN d.distance IS NOT NULL AND d.distance != 0 
                THEN (COALESCE(d.start_rated_range_km, 0) - COALESCE(d.end_rated_range_km, 0)) 
                    * (SELECT efficiency FROM cars WHERE id = %s) 
                    / d.distance * 1000
                ELSE NULL
            END AS consumption_kWh_km
        FROM drives d
        LEFT JOIN positions sp ON d.start_position_id = sp.id
        LEFT JOIN positions ep ON d.end_position_id = ep.id
        LEFT JOIN geofences sg ON d.start_geofence_id = sg.id
        LEFT JOIN geofences eg ON d.end_geofence_id = eg.id
        WHERE d.id = %s;
        """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (config.TZ, car_id, drive_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("查询 drive id=%s 失败: %s", drive_id, e)
        return None

def get_latest_charging_id(car_id: int, in_progress: bool = False) -> Optional[int]:
    """
    查询 charging_processes 表中当前最大的 id。
    如果表为空，返回 None。
    """
    sql = "SELECT MAX(id) FROM charging_processes WHERE car_id = %s AND end_date IS NOT NULL;"
    if in_progress:
        sql = "SELECT MAX(id) FROM charging_processes WHERE car_id = %s AND end_date IS NULL AND DATE(start_date) = CURRENT_DATE;"
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (car_id,))
                row = cur.fetchone()
                return row[0]
    except psycopg2.Error as e:
        logger.error("查询 charging_processes 最大 id 失败: %s", e)
        return None
    
def get_charging_by_id(charging_id: int) -> Optional[dict]:
    """
    根据 id 查询单条充电记录，返回字典（字段名 → 值）。
    查询不到时返回 None。
    """
    sql = """
        SELECT
            cp.id,
            COALESCE(cp.start_battery_level, p.battery_level) AS start_battery_level,
            cp.end_battery_level,
            CASE 
                WHEN cp.duration_min IS NOT NULL AND cp.duration_min != 0 
                THEN cp.charge_energy_added / cp.duration_min * 60
                ELSE NULL
            END AS average_power_kw,
            cp.duration_min,
            cp.end_ideal_range_km - cp.start_ideal_range_km AS range_added_km,
            p.latitude,
            p.longitude,
            cp.address_id,
            g.name AS geofence_name,
            CASE 
                WHEN (
                    SELECT charger_phases  FROM charges  WHERE charging_process_id = cp.id  ORDER BY id DESC LIMIT 1
                ) IS NULL THEN '直流'
                ELSE '交流'
            END AS charge_type
        FROM charging_processes cp
        LEFT JOIN positions p ON cp.position_id = p.id
        LEFT JOIN geofences g ON cp.geofence_id = g.id
        WHERE cp.id = %s;
        """
    try:
        with get_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(sql, (charging_id,))
                row = cur.fetchone()
                return dict(row) if row else None
    except psycopg2.Error as e:
        logger.error("查询 charging_process id=%s 失败: %s", charging_id, e)
        return None

def update_charging_address_id(charging_id: int, address_id: int) -> bool:
    """更新充电记录的地址 id"""
    sql = """
        UPDATE charging_processes
        SET address_id = %s
        WHERE id = %s
        """
    try:
        with get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, (address_id, charging_id,))
                conn.commit()
                return True
    except psycopg2.Error as e:
        logger.error("更新 charging_process id=%s 地址 id 失败: %s", charging_id, e)
        return False