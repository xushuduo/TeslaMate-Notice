import requests
import logging
from app.config import config

logger = logging.getLogger(__name__)

def bdmap_get_address_from_api(latitude: float, longitude: float, charging_station: bool = False) -> dict | None:
    """
    调用百度地图 API 逆地理编码，失败返回 None
    """
    try:
        params = {
            'ak': config.BAIDU_MAP_API_KEY,
            'extensions_poi': 1,
            'output': 'json',
            'coordtype': 'wgs84ll',
            'radius': 100,
            'location': f'{latitude},{longitude}'
        }
        if charging_station:
            params['poi_types'] = '充电站'
        logger.info(f"请求百度地图 API: {params}")
        resp = requests.get('https://api.map.baidu.com/reverse_geocoding/v3/', params=params, timeout=10)
        if resp.ok:
            data = resp.json()
            if data.get('status') == 0 and data.get('result'):
                fix_lat = data['result']['location']['lat']
                fix_lng = data['result']['location']['lng']
                province = data['result']['addressComponent'].get('province', '')
                city = data['result']['addressComponent'].get('city', '')
                district = data['result']['addressComponent'].get('district', '')
                township = data['result']['addressComponent'].get('town', '')
                road = data['result']['addressComponent'].get('street', {})
                display_name = data['result']['formatted_address_poi']
                name = display_name
                if data['result'].get('pois') and len(data['result']['pois']) > 0:
                    name = data['result']['pois'][0].get('name', name)
                else:
                    if province:
                        name = name.replace(province, '')
                    if city:
                        name = name.replace(city, '')
                    if district:
                        name = name.replace(district, '')
                    if township:
                        name = name.replace(township, '')
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
                    'raw': data['result'],
                }
        logger.error("百度地图 API 请求失败: %s, 响应: %s", resp.status_code, resp.text[:200])
    except requests.RequestException as e:
        logger.error("百度地图 API 请求异常: %s", e)
    return None