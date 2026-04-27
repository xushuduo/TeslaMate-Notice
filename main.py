"""
TeslaMateNotice 入口
"""
import logging
import threading
from app.monitor import run_monitor
from app.ws import run_ws

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

if __name__ == "__main__":
    t_ws = threading.Thread(target=run_ws, name="ws", daemon=True)
    t_monitor = threading.Thread(target=run_monitor, name="monitor", daemon=True)

    t_ws.start()
    t_monitor.start()

    t_ws.join()
    t_monitor.join()