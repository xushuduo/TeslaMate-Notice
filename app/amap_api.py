import requests
import logging
from app.tools import wgs84_to_gcj02
from app.config import config

logger = logging.getLogger(__name__)

def amap_get_address_from_api(latitude: float, longitude: float, charging_station: bool = False) -> dict | None:
    """
    调用高德地图 API 逆地理编码，失败返回 None
    """
    try:
        fix_lng, fix_lat = wgs84_to_gcj02(float(longitude), float(latitude))
        params = {
            'key': config.AMAP_API_KEY,
            'location': f'{fix_lng},{fix_lat}',
            'extensions': 'base',
        }
        if charging_station:
            params['poitype'] = '011100'
        logger.info(f"请求高德地图 API: {params}")
        resp = requests.get('https://restapi.amap.com/v3/geocode/regeo', params=params, timeout=10)
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
                name = display_name
                if province:
                    name = name.replace(province, '')
                if city:
                    name = name.replace(city, '')
                if district:
                    name = name.replace(district, '')
                if township:
                    name = name.replace(township, '')
                if road:
                    name = name.replace(road, '')
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