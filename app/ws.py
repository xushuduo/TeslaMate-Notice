import json
import re
import logging
from urllib.parse import urlencode
import websocket
import requests
from app.config import config
from app.notifier import send_notification
from app.address_fix import _get_address_from_api

logger = logging.getLogger(__name__)
phx_join_data = {}
latest_longitude = 0
latest_latitude = 0

def build_join_data(join_id, phx_id, phx_session, phx_static):
    return [
        join_id,
        join_id,
        'lv:' + phx_id,
        'phx_join',
        {
            'url': f"http://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}",
            'session': phx_session,
            'static': phx_static,
            'params': {
                '_csrf_token': phx_join_data['csrf_token'],
                'baseUrl': f"http://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}",
                'referrer': '',
                'tz': config.TZ,
                '_mounts': '0'
            }
        }
    ]

def on_open(ws, join_send_data):
    logger.info("TeslaMate WebSocket 已连接")
    ws.send(json.dumps(join_send_data, ensure_ascii=False, separators=(',', ':')))

def on_message(ws, msg):
    # logger.info(f'[MESSAGE] {msg}')
    if 'data-phx-session=' in msg:
        m = re.search(r'data-phx-session=\\"(.*?)\\"', msg)
        if m is None:
            logger.warning("data-phx-session 匹配失败，跳过 join")
        else:
            car_session = m.group(1)
            send_data = build_join_data(
                "10",
                "car_1",
                car_session,
                phx_join_data['car_static']
            )
            ws.send(json.dumps(send_data, ensure_ascii=False, separators=(',', ':')))
    if 'https://www.google.com/maps?q=' in msg:
        # 记录最新的经纬度信息，供后续发送通知时使用
        global latest_longitude, latest_latitude
        m = re.search(r'https://www\.google\.com/maps\?q=(.*?)\\"', msg)
        if m is None:
            logger.warning("maps?q= 匹配失败，跳过位置更新")
        else:
            location = m.group(1)
            if ',' in location:
                latest_latitude, latest_longitude = location.split(',')
            # logger.info(f"更新最新位置：经度={latest_longitude} 纬度={latest_latitude}")
    if 'Sentry Mode recording' in msg:
        # 哨兵模式开始录制，发送通知
        logger.info("检测到车辆哨兵模式开始录制")
        address_data = _get_address_from_api(latest_latitude, latest_longitude)
        content = '您的特斯拉哨兵模式正在录制中，请注意车辆周围环境安全。'
        if address_data is not None:
            content += f"\n地点：{address_data['name']}"
        send_notification('哨兵模式通知', content)
    elif 'Sentry Mode' in msg:
        logger.info("检测到车辆哨兵模式已开启")
    elif 'Plugged In' in msg: # 充电枪已插入
        logger.info("检测到车辆充电枪已插入")
    elif 'Driver present' in msg: # 驾驶员在车内
        logger.info("检测到驾驶员在车内")
    elif 'Unlocked' in msg: # 车辆已解锁
        logger.info("检测到车辆已解锁")
    elif 'Locked' in msg: # 车辆已锁定
        logger.info("检测到车辆已锁定")
    elif 'Doors open' in msg: # 车门已打开
        logger.info("检测到车辆车门已打开")
    elif '"charging"' in msg: # 充电状态变为charging
        logger.info("检测到车辆开始充电")
        # address_data = _get_address_from_api(latest_latitude, latest_longitude)
        # content = '您的特斯拉已开始充电。'
        # if address_data is not None:
        #     content += f"\n地点：{address_data['name']}"
        # send_notification('充电通知', content)
    
def on_error(ws, error):
    logger.error(f'TeslaMate WebSocket ERROR {error}')

def on_close(ws, close_status_code, close_msg):
    logger.info(f'TeslaMate WebSocket CLOSED code={close_status_code} msg={close_msg}')

def run_ws():
    r = requests.get(f"http://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}")
    html = r.text
    phx_join_data['csrf_token'] = re.search(r'<meta content="(.*?)" name="csrf-token">', html).group(1)
    phx_join_data['phx_id'], phx_join_data['phx_session'], phx_join_data['phx_static'] = re.search(r'id="(phx-[^"]+)" data-phx-session="([^"]+)" data-phx-static="([^"]+)"', html).groups()
    phx_join_data['car_static'] = re.search(r'id="car_1" data-phx-session="" data-phx-static="(.*?)"', html).group(1)
    join_send_data = build_join_data(
        "4",
        phx_join_data['phx_id'],
        phx_join_data['phx_session'],
        phx_join_data['phx_static']
    )
    cookie = '; '.join([f"{k}={v}" for k, v in r.cookies.items()])
    params = urlencode({
        "_csrf_token": phx_join_data['csrf_token'],
        "vsn": "2.0.0"
    })
    ws = websocket.WebSocketApp(
        f"ws://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}/live/websocket?{params}",
        header={
            "Cookie": cookie,
        },
        on_open=lambda ws: on_open(ws, join_send_data),
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(ping_interval=30, ping_timeout=10, reconnect=5)

if __name__ == "__main__":
    run_ws()
