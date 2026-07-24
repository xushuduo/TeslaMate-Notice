"""
推送通知模块: 支持 TETE 和 Bark 两个平台
"""
import logging
import requests
import threading
from app.config import config
from app.tools import format_minutes
from app.db import get_drive_trace_by_id
from urllib.parse import urlencode

logger = logging.getLogger(__name__)

def bark_push(title: str, content: str, extras: dict = None) -> bool:
    if not config.BARK_PUSH_API_URL:
        logger.warning("未配置 Bark 推送 URL，跳过推送")
        return False
    try:
        data = {"title": title, "body": content, "group": "teslamate", "icon": config.BARK_PUSH_ICON_URL, **(extras or {})}
        resp = requests.post(config.BARK_PUSH_API_URL, json=data, timeout=10)
        if resp.ok:
            logger.info("Bark 推送成功: %s", data['title'])
            return True
        else:
            logger.warning("Bark 推送失败，状态码: %d，响应: %s", resp.status_code, resp.text[:200])
    except requests.RequestException as e:
        logger.error("Bark 推送请求异常: %s", e)
    return False

def tete_push(title: str, content: str) -> bool:
    if not config.TETE_PUSH_API_URL:
        logger.warning("未配置 TETE 推送 URL，跳过推送")
        return False
    try:
        data = {"title": title, "content": content}
        resp = requests.post(config.TETE_PUSH_API_URL, json=data, timeout=10)
        if resp.ok:
            logger.info("TETE 推送成功: %s", data['title'])
            return True
        else:
            logger.warning("TETE 推送失败，状态码: %d，响应: %s", resp.status_code, resp.text[:200])
    except requests.RequestException as e:
        logger.error("TETE 推送请求异常: %s", e)
    return False

def send_drive_notification(car_name: str, drive_data: dict) -> None:
    title = f'[{car_name}]行程通知'
    contents = [
        f"时间: {drive_data['start_date_str']} | 耗时: {format_minutes(drive_data['duration_min'])} | 里程: {drive_data['distance']:.2f} km",
        f"电量: {drive_data['start_battery_level']}% → {drive_data['end_battery_level']}% | 能耗: {drive_data['consumption_kwh_km']:.0f} Wh/km",
    ]
    if drive_data['start_geofence_name'] is not None and drive_data['end_geofence_name'] is not None:
        if 'start_geofence_name_city' in drive_data and drive_data['start_geofence_name_city'] and 'end_geofence_name_city' in drive_data and drive_data['end_geofence_name_city'] and drive_data['start_geofence_name_city'] != drive_data['end_geofence_name_city']:
            contents.append(f"路程: {drive_data['start_geofence_name_city']}·{drive_data['start_geofence_name']} → {drive_data['end_geofence_name_city']}·{drive_data['end_geofence_name']}")
        else:
            contents.append(f"路程: {drive_data['start_geofence_name']} → {drive_data['end_geofence_name']}")
    content = "\n".join(contents)
    threading.Thread(target=tete_push, args=(title, content)).start()
    extras = {}
    if config.BAIDU_MAP_API_KEY and config.PUSH_DRIVE_TRACK:
        traces = get_drive_trace_by_id(drive_data['id'])
        if traces:
            startLocation = f"{traces[0]['longitude']},{traces[0]['latitude']}"
            endLocation = f"{traces[-1]['longitude']},{traces[-1]['latitude']}"
            params = {
                'ak': config.BAIDU_MAP_API_KEY,
                'coordtype': 'wgs84ll',
                'copyright': 1,
                'scaler': 2,
                'width': 300,
                'height': 400,
                'pathStyles': '0x00c957,8,1',
                'markers': f"{startLocation}|{endLocation}",
                'markerStyles': 'l|l',
                'labels': f"{startLocation}|{endLocation}",
                'labelStyles': f"{drive_data['start_geofence_name']},0,25,0x000000,,1|{drive_data['end_geofence_name']},0,25,0x000000,,1",
                'paths': ';'.join(f"{trace['longitude']},{trace['latitude']}" for trace in traces)
            }
            extras['image'] = 'https://api.map.baidu.com/staticimage/v2?' + urlencode(params)
    threading.Thread(target=bark_push, args=(title, content, extras)).start()

def send_charging_completion_notification(car_name: str, charging_data: dict) -> None:
    title = f'[{car_name}]充电完成通知'
    contents = [
        f"电量: {charging_data['start_battery_level']}% → {charging_data['end_battery_level']}% | 平均功率: {charging_data['average_power_kw']:.1f} kW",
        f"耗时: {format_minutes(charging_data['duration_min'])} | 增加续航: {charging_data['range_added_km']:.0f} km",
    ]
    if charging_data['geofence_name'] is not None:
        contents.append(f"地点: {charging_data['geofence_name']}")
    content = "\n".join(contents)
    threading.Thread(target=tete_push, args=(title, content)).start()
    threading.Thread(target=bark_push, args=(title, content)).start()

def send_charging_start_notification(car_name: str, charging_data: dict, icon: str = None, push_tete: bool = True) -> None:
    title = f'[{car_name}]开始充电通知'
    contents = [
        f"起始电量: {charging_data['start_battery_level']}%",
        f"充电类型: {charging_data['charge_type']}",
    ]
    if charging_data['geofence_name'] is not None:
        contents.append(f"地点: {charging_data['geofence_name']}")
    content = "\n".join(contents)
    if push_tete:
        threading.Thread(target=tete_push, args=(title, content)).start()
    extras = {
        'id': 'teslamate-charging-id-%d' % charging_data['id'],
        'level': 'passive'
    }
    if icon:
        extras['icon'] = icon
    threading.Thread(target=bark_push, args=(title, content, extras)).start()

def send_notification(title: str, content: str) -> None:
    if not title or not content:
        logger.debug("title 或 content 为空，跳过推送")
        return
    threading.Thread(target=tete_push, args=(title, content)).start()
    threading.Thread(target=bark_push, args=(title, content)).start()