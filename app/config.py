"""
配置模块：从环境变量读取所有配置项
"""
import os


class Config:
    # TeslaMate 连接配置
    TESLAMATE_HOST: str = os.getenv("TESLAMATE_HOST", "teslamate")
    TESLAMATE_PORT: int = int(os.getenv("TESLAMATE_PORT", "4000"))
    
    # PostgreSQL 连接配置
    DB_HOST: str = os.getenv("DATABASE_HOST", "database")
    DB_PORT: int = int(os.getenv("DATABASE_PORT", "5432"))
    DB_NAME: str = os.getenv("DATABASE_NAME", "teslamate")
    DB_USER: str = os.getenv("DATABASE_USER", "teslamate")
    DB_PASSWORD: str = os.getenv("DATABASE_PASS", "password")

    # 推送平台 URL（留空则不推送）
    TETE_PUSH_API_URL: str = os.getenv("TETE_PUSH_API_URL", "")
    BARK_PUSH_API_URL: str = os.getenv("BARK_PUSH_API_URL", "")
    # 请求重试次数
    RETRY_COUNT: int = int(os.getenv("RETRY_COUNT", "5"))
    # 请求重试间隔（秒）
    RETRY_INTERVAL: int = int(os.getenv("RETRY_INTERVAL", "10"))

    # 高德地图 API KEY
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")

    # 车辆 ID
    CAR_ID: int = int(os.getenv("CAR_ID", "1"))

    # 轮询间隔（秒）
    POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "10"))

    # 行程推送门槛 最小行驶公里数
    MIN_DRIVE_DISTANCE_KM: float = float(os.getenv("MIN_DRIVE_DISTANCE_KM", "1.0"))
    # 行程推送门槛 最小行驶时间（分钟）
    MIN_DRIVE_DURATION_MIN: int = int(os.getenv("MIN_DRIVE_DURATION_MIN", "1"))

    # 时区
    TZ: str = os.getenv("TZ", "Asia/Shanghai")

    @property
    def db_dsn(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


config = Config()
