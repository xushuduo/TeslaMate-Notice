"""
行程监控模块：轮询 drives 表，检测新行程并触发通知
"""
import logging
import time
from app.config import config
from app.db import get_latest_drive_id, get_drive_by_id, get_latest_charging_id, get_charging_by_id
from app.notifier import send_notification
from app.address_fix import fix_drive_addresses, fix_charging_addresses
from app.tools import format_minutes

logger = logging.getLogger(__name__)

def format_drive_content(data: dict) -> str:
    """
    时间：23:23 | 耗时：14分钟 | 里程：15.8km\n电量：75% → 60% | 能耗：123 Wh/km\n路程：中山路 → 机场路
    """
    lines = [
        f"时间：{data['start_date_str']} | 耗时：{format_minutes(data['duration_min'])} | 里程：{data['distance']:.2f} km",
        f"电量：{data['start_battery_level']}% → {data['end_battery_level']}% | 能耗：{data['consumption_kwh_km']:.0f} Wh/km",
    ]
    if data['start_address_id'] is None or data['end_address_id'] is None:
        fix_drive_addresses(data)
    if data['start_geofence_name'] is None or data['end_geofence_name'] is None:
        fix_drive_addresses(data)
    if data['start_geofence_name'] is not None and data['end_geofence_name'] is not None:
        lines.append(f"路程：{data['start_geofence_name']} → {data['end_geofence_name']}")
    return "\n".join(lines)

def format_charging_completion_content(data: dict) -> str:
    """
    电量：60% → 70% | 平均功率：6.9 kW\n耗时：7 小时 | 增加续航：250 km\n充电地点：中山路
    """
    lines = [
        f"电量：{data['start_battery_level']}% → {data['end_battery_level']}% | 平均功率：{data['average_power_kw']:.1f} kW",
        f"耗时：{format_minutes(data['duration_min'])} | 增加续航：{data['range_added_km']:.0f} km",
    ]
    if data['address_id'] is None or data['geofence_name'] is None:
        fix_charging_addresses(data)
    if data['geofence_name'] is not None:
        lines.append(f"地点：{data['geofence_name']}")
    return "\n".join(lines)

def format_charging_start_content(data: dict) -> str:
    """
    电量：起始电量：60%\n充电类型：交流\n充电地点：中山路
    """
    lines = [
        f"起始电量：{data['start_battery_level']}%",
        f"充电类型：{data['charge_type']}",
    ]
    if data['address_id'] is None or data['geofence_name'] is None:
        fix_charging_addresses(data)
    if data['geofence_name'] is not None:
        lines.append(f"地点：{data['geofence_name']}")
    return "\n".join(lines)

def run_monitor() -> None:
    """
    监控主循环：
      1. 启动时记录当前最大 drive id 作为基准
      2. 每隔 POLL_INTERVAL 秒查询一次最新 id
      3. 若 id 有增长，依次获取新行程详情并推送通知
    """
    logger.info("行程监控启动，轮询间隔 %d 秒", config.POLL_INTERVAL)

    latest_drive_id: int = 0
    while True:
        latest_drive_id = get_latest_drive_id()
        if latest_drive_id is not None:
            logger.info("数据库已就绪，当前最大行程id = %s", latest_drive_id)
            break
        logger.warning("数据库未就绪或 drives 表为空，%d 秒后重试…", config.POLL_INTERVAL)
        time.sleep(config.POLL_INTERVAL)
    
    latest_charging_completion_id: int = 0
    while True:
        latest_charging_completion_id = get_latest_charging_id()
        if latest_charging_completion_id is not None:
            logger.info("数据库已就绪，当前最大充电完成id = %s", latest_charging_completion_id)
            break
        logger.warning("数据库未就绪或 charging_processes 表为空，%d 秒后重试…", config.POLL_INTERVAL)
        time.sleep(config.POLL_INTERVAL)
    
    latest_charging_start_id: int = 0
    while True:
        latest_charging_start_id = get_latest_charging_id(True)
        logger.info("数据库已就绪，当前最大充电中id = %s", latest_charging_start_id)
        break

    while True:
        time.sleep(config.POLL_INTERVAL)

        # 行程监测
        current_drive_id = get_latest_drive_id()
        if current_drive_id is not None:
            if current_drive_id > latest_drive_id:
                logger.info("检测到新行程，当前最大行程id = %s", current_drive_id)
                drive = get_drive_by_id(current_drive_id)
                if drive is not None:
                    latest_drive_id = current_drive_id
                    drive_data = get_drive_by_id(current_drive_id)
                    if drive_data['duration_min'] > config.MIN_DRIVE_DURATION_MIN and drive_data['distance'] > config.MIN_DRIVE_DISTANCE_KM:
                        # 推送通知
                        content = format_drive_content(drive_data)
                        send_notification('行程通知', content)
                    else:
                        logger.info("新行程 id=%s 不满足最小持续时间或最小行驶距离要求，跳过推送", current_drive_id)
                        if drive_data['start_address_id'] is None or drive_data['end_address_id'] is None:
                            fix_drive_addresses(drive_data)
                else:
                    logger.warning("drive id=%s 查询不到，跳过", current_drive_id)
            # else:
            #     logger.info("无新行程，当前最大 drive id = %s", current_drive_id)
        else:
            logger.warning("查询最新 drive id 失败，%d 秒后重试…", config.POLL_INTERVAL)
        
        # 充电完成监测
        current_charging_completion_id = get_latest_charging_id()
        if current_charging_completion_id is not None:
            if current_charging_completion_id > latest_charging_completion_id:
                logger.info("检测到新充电记录，当前最大充电完成id = %s", current_charging_completion_id)
                charging = get_charging_by_id(current_charging_completion_id)
                if charging is not None:
                    latest_charging_completion_id = current_charging_completion_id
                    charging_data = get_charging_by_id(current_charging_completion_id)
                    # 推送通知
                    content = format_charging_completion_content(charging_data)
                    send_notification('充电完成通知', content)
                else:
                    logger.warning("charging completion id=%s 查询不到，跳过", current_charging_completion_id)
            # else:
            #     logger.info("无新充电记录，当前最大 charging completion id = %s", current_charging_completion_id)
        else:
            logger.warning("查询最新 charging completion id 失败，%d 秒后重试…", config.POLL_INTERVAL)

        # 充电中监测
        current_charging_start_id = get_latest_charging_id(True)
        # logger.info("查询最新 charging start id = %s", current_charging_start_id)
        if current_charging_start_id is not None:
            if current_charging_start_id > latest_charging_start_id:
                logger.info("检测到新充电中记录，当前最大充电中id = %s", current_charging_start_id)
                charging = get_charging_by_id(current_charging_start_id)
                if charging is not None:
                    latest_charging_start_id = current_charging_start_id
                    charging_data = get_charging_by_id(current_charging_start_id)
                    # 推送通知
                    content = format_charging_start_content(charging_data)
                    send_notification('开始充电通知', content)
                else:
                    logger.warning("charging start id=%s 查询不到，跳过", current_charging_start_id)
            # else:
            #     logger.info("无新充电中记录，当前最大 charging start id = %s", current_charging_start_id)


