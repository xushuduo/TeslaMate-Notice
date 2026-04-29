"""
TeslaMateNotice 入口
"""
import logging
import threading
import requests
import re
from app.monitor import run_monitor
from app.ws import run_ws
from app.config import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    resp = requests.get(f"http://{config.TESLAMATE_HOST}:{config.TESLAMATE_PORT}")
    result = resp.text
    if '<div id="car_' in result:
        car_data = result.split('<div id="car_')
        if len(car_data) > 1:
            threads = []
            for item in car_data[1:]:
                car_id = item.split('"')[0]
                if config.CAR_ID != "ALL":
                    if str(config.CAR_ID) != car_id:
                        continue
                m_title = re.search(r'<p class="title is-5">(.*?)</p>', item)
                car_title = m_title.group(1) if m_title else None
                if not car_title:
                    m_sub = re.search(r'<p class="subtitle is-6 has-text-weight-light">(.*?)</p>', item)
                    car_title = m_sub.group(1) if m_sub else None
                if not car_title:
                    car_title = "特斯拉车辆%s" % car_id
                logging.info(f"[CAR_{car_id}]检测到车辆：{car_title}")
                t_ws = threading.Thread(target=run_ws, args=(int(car_id), car_title,), name=f"ws_{car_id}", daemon=True)
                t_monitor = threading.Thread(target=run_monitor, args=(int(car_id), car_title,), name=f"monitor_{car_id}", daemon=True)
                t_ws.start()
                t_monitor.start()
                threads.extend([t_ws, t_monitor])
            if len(threads) > 0:
                for t in threads:
                    t.join()
            else:
                logging.error("未检测到车辆信息，无法启动监控")
        else:
            logging.error("未检测到车辆信息，无法启动监控")
    else:
        logging.error("未检测到车辆信息，无法启动监控")

