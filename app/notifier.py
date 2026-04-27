"""
推送通知模块：支持 TETE 和 Bark 两个平台
"""
import logging
import requests
import time
import threading
from app.config import config

logger = logging.getLogger(__name__)


def _post(url: str, title: str, content: str, platform: str) -> bool:
    """向指定 URL 发送 POST 推送请求"""
    if platform == "BARK":
        data = {"title": title, "body": content}
    else:
        data = {"title": title, "content": content}
    logger.info("[%s]开始推送: %s", platform, data)
    for _ in range(config.RETRY_COUNT):
        try:
            resp = requests.post(url, json=data,timeout=10)
            if resp.ok:
                logger.info("[%s]推送成功: %s", platform, title)
                return True
            else:
                logger.warning("[%s]推送失败，状态码: %d，响应: %s", platform, resp.status_code, resp.text[:200])
        except requests.RequestException as e:
            logger.error("[%s]推送请求异常: %s", platform, e)
        time.sleep(config.RETRY_INTERVAL)
    return False


def send_notification(title: str, content: str) -> None:
    """
    向所有已配置的平台发送通知。
    title  : 通知标题
    content: 通知正文（调用方负责组装）
    """
    if not title or not content:
        logger.debug("title 或 content 为空，跳过推送")
        return

    if config.TETE_PUSH_API_URL and config.TETE_PUSH_API_URL != "":
        threading.Thread(target=_post, args=(config.TETE_PUSH_API_URL, title, content, "TETE")).start()

    if config.BARK_PUSH_API_URL and config.BARK_PUSH_API_URL != "":
        threading.Thread(target=_post, args=(config.BARK_PUSH_API_URL, title, content, "BARK")).start()

    if not config.TETE_PUSH_API_URL and not config.BARK_PUSH_API_URL:
        logger.warning("未配置任何推送 URL，通知未发送: %s", title)
