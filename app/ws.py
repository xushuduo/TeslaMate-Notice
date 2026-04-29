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

def build_join_data(join_id, phx_id, phx_session, phx_static, car_id, local_phx_join_data):
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
                '_csrf_token': local_phx_join_data['csrf_token'],
                'baseUrl': f"http://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}",
                'referrer': '',
                'tz': config.TZ,
                '_mounts': '0'
            }
        }
    ]

def make_on_open(join_send_data, car_name):
    def on_open(ws):
        logger.info(f"[{car_name}]TeslaMate WebSocket 已连接")
        ws.send(json.dumps(join_send_data, ensure_ascii=False, separators=(',', ':')))
    return on_open

def make_on_message(car_id, car_name, local_phx_join_data):
    state = {'latest_longitude': 0, 'latest_latitude': 0}

    def on_message(ws, msg):
        # logger.info(f'[MESSAGE] {msg}')
        if 'data-phx-session=' in msg:
            m = re.search(r'data-phx-session=\\"(.*?)\\"', msg)
            if m is None:
                logger.warning(f"[{car_name}]data-phx-session 匹配失败，跳过 join")
            else:
                car_session = m.group(1)
                send_data = build_join_data(
                    "10",
                    "car_%s" % car_id,
                    car_session,
                    local_phx_join_data['car_static'],
                    car_id,
                    local_phx_join_data,
                )
                ws.send(json.dumps(send_data, ensure_ascii=False, separators=(',', ':')))
        if 'https://www.google.com/maps?q=' in msg:
            m = re.search(r'https://www\.google\.com/maps\?q=(.*?)\\"', msg)
            if m is None:
                logger.warning(f"[{car_name}]maps?q= 匹配失败，跳过位置更新")
            else:
                location = m.group(1)
                if ',' in location:
                    state['latest_latitude'], state['latest_longitude'] = location.split(',')
                # logger.info(f"更新最新位置：经度={state['latest_longitude']} 纬度={state['latest_latitude']}")
        if 'Sentry Mode recording' in msg:
            logger.info(f"[{car_name}]检测到车辆哨兵模式开始录制")
            address_data = _get_address_from_api(state['latest_latitude'], state['latest_longitude'])
            content = '您的特斯拉哨兵模式正在录制中，请注意车辆周围环境安全。'
            if address_data is not None:
                content += f"\n地点：{address_data['name']}"
            send_notification(f'[{car_name}]哨兵模式通知', content)
        elif 'Sentry Mode' in msg:
            logger.info(f"[{car_name}]检测到车辆哨兵模式已开启")
        elif 'Plugged In' in msg:
            logger.info(f"[{car_name}]检测到车辆充电枪已插入")
        elif 'Driver present' in msg:
            logger.info(f"[{car_name}]检测到驾驶员在车内")
        elif 'Unlocked' in msg:
            logger.info(f"[{car_name}]检测到车辆已解锁")
        elif 'Locked' in msg:
            logger.info(f"[{car_name}]检测到车辆已锁定")
        elif 'Doors open' in msg:
            logger.info(f"[{car_name}]检测到车辆车门已打开")
        elif '"charging"' in msg:
            logger.info(f"[{car_name}]检测到车辆开始充电")

    return on_message
    
def on_error(ws, error):
    logger.error(f'TeslaMate WebSocket ERROR {error}')

def on_close(ws, close_status_code, close_msg):
    logger.info(f'TeslaMate WebSocket CLOSED code={close_status_code} msg={close_msg}')

def run_ws(CAR_ID: int = 1, CAR_NAME: str = "未知车辆") -> None:
    car_id = CAR_ID
    car_name = CAR_NAME
    local_phx_join_data = {}
    r = requests.get(f"http://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}")
    html = r.text
    if 'car_%s' % car_id not in html:
        logger.error(f"[{car_name}]检测不到 car_{car_id}，WebSocket 连接失败")
        return
    local_phx_join_data['csrf_token'] = re.search(r'<meta content="(.*?)" name="csrf-token">', html).group(1)
    local_phx_join_data['phx_id'], local_phx_join_data['phx_session'], local_phx_join_data['phx_static'] = re.search(r'id="(phx-[^"]+)" data-phx-session="([^"]+)" data-phx-static="([^"]+)"', html).groups()
    local_phx_join_data['car_static'] = re.search(r'id="car_%s" data-phx-session="" data-phx-static="(.*?)"' % car_id, html).group(1)
    join_send_data = build_join_data(
        "4",
        local_phx_join_data['phx_id'],
        local_phx_join_data['phx_session'],
        local_phx_join_data['phx_static'],
        car_id,
        local_phx_join_data,
    )
    cookie = '; '.join([f"{k}={v}" for k, v in r.cookies.items()])
    params = urlencode({
        "_csrf_token": local_phx_join_data['csrf_token'],
        "vsn": "2.0.0"
    })
    ws = websocket.WebSocketApp(
        f"ws://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}/live/websocket?{params}",
        header={
            "Cookie": cookie,
        },
        on_open=make_on_open(join_send_data, car_name),
        on_message=make_on_message(car_id, car_name, local_phx_join_data),
        on_error=on_error,
        on_close=on_close,
    )
    ws.run_forever(ping_interval=30, ping_timeout=10, reconnect=5)

if __name__ == "__main__":
    run_ws()
