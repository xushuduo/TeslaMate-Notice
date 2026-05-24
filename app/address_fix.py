import logging
import requests
from app.config import config
from app.db import (
    get_address_by_location,
    get_address_by_id,
    insert_address,
    update_drive_address_id,
    update_charging_address_id,
)
from app.amap_api import amap_get_address_from_api
from app.bdmap_api import bdmap_get_address_from_api

logger = logging.getLogger(__name__)

def update_address_name(address_data: dict, update_data: dict, update_key_name: str) -> None:
    """
    按优先级（name > road > township > district > city > province）
    填充 update_data[update_key_name]，仅当目标字段为空时才写入。
    """
    if address_data and 'city' in address_data and address_data['city'] and update_data:
        update_data[update_key_name + '_city'] = address_data.get('city', '')
    if update_data.get(update_key_name):
        return
    for field in ('name', 'road', 'township', 'district', 'city', 'province'):
        value = address_data.get(field)
        if value:
            update_data[update_key_name] = value
            return

def _resolve_address(
    data: dict,
    lat_key: str,
    lng_key: str,
    address_id_key: str,
    geofence_name_key: str
) -> None:
    """
    通用地址修复逻辑：
      - 若 address_id 为空，通过经纬度查库；
      - 若库中地址来自 OSM 或不存在，调用高德 API 重新入库；
      - 最终将 name 填入 geofence_name。
    """
    need_new = False
    address_data = None

    if data[address_id_key] is None:
        address_data = get_address_by_location(data[lat_key], data[lng_key])
        if address_data is None or address_data.get('is_openstreetmap'):
            need_new = True
        else:
            data[address_id_key] = address_data['id']
            update_address_name(address_data, data, geofence_name_key)
    else:
        address_data = get_address_by_id(data[address_id_key])
        if address_data is None or address_data.get('is_openstreetmap'):
            need_new = True
        else:
            update_address_name(address_data, data, geofence_name_key)

    if need_new:
        charging_station = False
        if 'start_battery_level' in data and 'charge_type' in data and data['charge_type'] == '直流':
            # 快充优先获取充电站POI
            charging_station = True
        map_data = None
        if config.BAIDU_MAP_API_KEY:
            map_data = bdmap_get_address_from_api(data[lat_key], data[lng_key], charging_station)
        if map_data is None and config.AMAP_API_KEY:
            map_data = amap_get_address_from_api(data[lat_key], data[lng_key], charging_station)
        if map_data is None:
            logger.error("地图 API 返回空，地址修复失败")
            return
        logger.info("地图 API 返回地址信息，修复成功")
        new_id = insert_address(map_data)
        data[address_id_key] = new_id
        update_address_name(map_data, data, geofence_name_key)

def fix_drive_addresses(data: dict) -> bool:
    if not config.AMAP_API_KEY and not config.BAIDU_MAP_API_KEY:
        logger.warning("未配置高德地图 API KEY 或百度地图 API KEY")
        if data['start_address_id']:
            address_data = get_address_by_id(data['start_address_id'])
            if address_data:
                update_address_name(address_data, data, 'start_geofence_name')
        if data['end_address_id']:
            address_data = get_address_by_id(data['end_address_id'])
            if address_data:
                update_address_name(address_data, data, 'end_geofence_name')
        return True
    
    logger.info("行程%s，尝试修复地址信息", data['id'])
    _resolve_address(data, 'start_latitude', 'start_longitude', 'start_address_id', 'start_geofence_name')
    _resolve_address(data, 'end_latitude', 'end_longitude', 'end_address_id', 'end_geofence_name')

    update_drive_address_id(data['id'], data['start_address_id'], data['end_address_id'])
    return True

def fix_charging_addresses(data: dict) -> bool:
    if not config.AMAP_API_KEY and not config.BAIDU_MAP_API_KEY:
        logger.warning("未配置高德地图 API KEY 或百度地图 API KEY")
        if data['address_id']:
            address_data = get_address_by_id(data['address_id'])
            if address_data:
                update_address_name(address_data, data, 'geofence_name')
        return True
    
    logger.info("充电%s，尝试修复地址信息", data['id'])
    _resolve_address(data, 'latitude', 'longitude', 'address_id', 'geofence_name')
    update_charging_address_id(data['id'], data['address_id'])
    return True