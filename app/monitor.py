"""
行程监控模块：轮询 drives 表，检测新行程并触发通知
"""
import logging
import time
from app.config import config
from app.db import get_latest_drive_id, get_drive_by_id, get_latest_charging_id, get_charging_by_id
from app.notifier import send_notification, send_drive_notification, send_charging_completion_notification, send_charging_start_notification
from app.address_fix import fix_drive_addresses, fix_charging_addresses

logger = logging.getLogger(__name__)

def run_monitor(CAR_ID: int = 1, CAR_NAME: str = "未知车辆") -> None:
    """
    监控主循环：
      1. 启动时记录当前最大 drive id 作为基准
      2. 每隔 POLL_INTERVAL 秒查询一次最新 id
      3. 若 id 有增长，依次获取新行程详情并推送通知
    """

    car_id = CAR_ID
    car_name = CAR_NAME

    logger.info(f"[{car_name}]行程监控启动，轮询间隔 {config.POLL_INTERVAL} 秒")

    latest_drive_id: int = 0
    while True:
        latest_drive_id = get_latest_drive_id(car_id)
        if latest_drive_id is not None:
            logger.info(f"[{car_name}]数据库已就绪，当前最大行程id = {latest_drive_id}")
            break
        logger.warning(f"[{car_name}]数据库未就绪或 drives 表为空，{config.POLL_INTERVAL} 秒后重试…")
        time.sleep(config.POLL_INTERVAL)
    
    latest_charging_completion_id: int = 0
    while True:
        latest_charging_completion_id = get_latest_charging_id(car_id)
        if latest_charging_completion_id is not None:
            logger.info(f"[{car_name}]数据库已就绪，当前最大充电完成id = {latest_charging_completion_id}")
            break
        logger.warning(f"[{car_name}]数据库未就绪或 charging_processes 表为空，{config.POLL_INTERVAL} 秒后重试…")
        time.sleep(config.POLL_INTERVAL)
    
    latest_charging_start_id = get_latest_charging_id(car_id, True)
    if latest_charging_start_id is None:
        latest_charging_start_id = 0
    logger.info(f"[{car_name}]数据库已就绪，当前最大充电中id = {latest_charging_start_id}")

    while True:
        time.sleep(config.POLL_INTERVAL)

        # 行程监测
        current_drive_id = get_latest_drive_id(car_id)
        if current_drive_id is not None:
            if current_drive_id > latest_drive_id:
                logger.info(f"[{car_name}]检测到新行程，当前最大行程id = {current_drive_id}")
                drive_data = get_drive_by_id(car_id, current_drive_id)
                if drive_data is not None:
                    latest_drive_id = current_drive_id
                    if drive_data['start_address_id'] is None or drive_data['end_address_id'] is None:
                        # 地址修复
                        fix_drive_addresses(drive_data)
                    if drive_data['duration_min'] > config.MIN_DRIVE_DURATION_MIN and drive_data['distance'] > config.MIN_DRIVE_DISTANCE_KM:
                        if drive_data['start_geofence_name'] is None or drive_data['end_geofence_name'] is None:
                            # 地址修复
                            fix_drive_addresses(drive_data)
                        # 推送通知
                        send_drive_notification(car_name, drive_data)
                    else:
                        logger.info(f"[{car_name}]新行程 id={current_drive_id} 不满足最小持续时间或最小行驶距离要求，跳过推送")
                else:
                    logger.warning(f"[{car_name}]drive id={current_drive_id} 查询不到，跳过")
            # else:
            #     logger.info(f"[{car_name}]无新行程，当前最大 drive id = {current_drive_id}")
        else:
            logger.warning(f"[{car_name}]查询最新 drive id 失败，{config.POLL_INTERVAL} 秒后重试…")
        
        # 充电完成监测
        current_charging_completion_id = get_latest_charging_id(car_id)
        if current_charging_completion_id is not None:
            if current_charging_completion_id > latest_charging_completion_id:
                logger.info(f"[{car_name}]检测到新充电记录，当前最大充电完成id = {current_charging_completion_id}")
                charging_data = get_charging_by_id(current_charging_completion_id)
                if charging_data is not None:
                    latest_charging_completion_id = current_charging_completion_id
                    # 推送通知
                    send_charging_completion_notification(car_name, charging_data)
                else:
                    logger.warning(f"[{car_name}]charging completion id={current_charging_completion_id} 查询不到，跳过")
            # else:
            #     logger.info(f"[{car_name}]无新充电记录，当前最大 charging completion id = {current_charging_completion_id}")
        else:
            logger.warning(f"[{car_name}]查询最新 charging completion id 失败，{config.POLL_INTERVAL} 秒后重试…")

        # 充电中监测
        current_charging_start_id = get_latest_charging_id(car_id, True)
        # logger.info(f"[{car_name}]查询最新 charging start id = {current_charging_start_id}")
        if current_charging_start_id is not None:
            if current_charging_start_id > latest_charging_start_id:
                logger.info(f"[{car_name}]检测到新充电中记录，当前最大充电中id = {current_charging_start_id}")
                charging_data = get_charging_by_id(current_charging_start_id)
                if charging_data is not None:
                    if charging_data['address_id'] is None or charging_data['geofence_name'] is None:
                        # 地址修复
                        fix_charging_addresses(charging_data)
                    latest_charging_start_id = current_charging_start_id
                    # 推送通知
                    send_charging_start_notification(car_name, charging_data)
                else:
                    logger.warning(f"[{car_name}]charging start id={current_charging_start_id} 查询不到，跳过")
            # else:
            #     logger.info(f"[{car_name}]无新充电中记录，当前最大 charging start id = {current_charging_start_id}")


