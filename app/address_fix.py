import logging
import requests
from app.config import config
from app.db import *
from app.tools import wgs84_to_gcj02

logger = logging.getLogger(__name__)

def _get_address_from_api(latitude: float, longitude: float) -> dict | None:

    """
    调用高德地图 API 逆地理编码，失败返回 None
    """
    try:
        fix_lng, fix_lat = wgs84_to_gcj02(float(longitude), float(latitude))
        logger.info(f"请求高德地图 API: {fix_lat}, {fix_lng}")
        resp = requests.get('https://restapi.amap.com/v3/geocode/regeo', params={
            'key': config.AMAP_API_KEY,
            'location': f'{fix_lng},{fix_lat}',
            'extensions': 'base',
        }, timeout=10)
        if resp.ok:
            data = resp.json()
            if data.get('status') == '1' and data.get('regeocode'):
                province = data['regeocode']['addressComponent'].get('province', '')
                city = data['regeocode']['addressComponent'].get('city', '')
                district = data['regeocode']['addressComponent'].get('district', '')
                township = data['regeocode']['addressComponent'].get('township', '')
                streetNumber = data['regeocode']['addressComponent'].get('streetNumber', {})
                road = ''
                if isinstance(streetNumber.get('street'), str) and isinstance(streetNumber.get('number'), str):
                    road = f"{streetNumber['street']}{streetNumber['number']}"
                display_name = data['regeocode']['formatted_address']
                name = display_name.replace(province, '').replace(city, '').replace(district, '').replace(township, '').replace(road, '')
                return {
                    'display_name': display_name,
                    'latitude': latitude,
                    'longitude': longitude,
                    'fix_latitude': fix_lat,
                    'fix_longitude': fix_lng,
                    'name': name,
                    'road': road,
                    'township': township,
                    'city': city,
                    'district': district,
                    'province': province,
                    'raw': data['regeocode'],
                }
        logger.error("高德地图 API 请求失败: %s, 响应: %s", resp.status_code, resp.text[:200])
    except requests.RequestException as e:
        logger.error("高德地图 API 请求异常: %s", e)
    return None

def update_address_name(address_data: dict, update_data: dict, update_key_name: str) -> None:
    """
    按优先级（name > road > township > district > city > province）
    填充 update_data[update_key_name]，仅当目标字段为空时才写入。
    """
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
        amap_data = _get_address_from_api(data[lat_key], data[lng_key])
        if amap_data is None:
            logger.error("高德 API 返回空，地址修复失败")
            return
        logger.info("高德 API 返回地址信息，修复成功")
        new_id = insert_address(amap_data)
        data[address_id_key] = new_id
        update_address_name(amap_data, data, geofence_name_key)

def fix_drive_addresses(data: dict) -> bool:
    if not config.AMAP_API_KEY:
        logger.warning("未配置高德地图 API KEY")
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
    if not config.AMAP_API_KEY:
        logger.warning("未配置高德地图 API KEY")
        if data['address_id']:
            address_data = get_address_by_id(data['address_id'])
            if address_data:
                update_address_name(address_data, data, 'geofence_name')
        return True
    
    logger.info("充电%s，尝试修复地址信息", data['id'])
    _resolve_address(data, 'latitude', 'longitude', 'address_id', 'geofence_name')
    update_charging_address_id(data['id'], data['address_id'])
    return True