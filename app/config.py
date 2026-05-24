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
    BARK_PUSH_ICON_URL: str = os.getenv("BARK_PUSH_ICON_URL", "https://is1-ssl.mzstatic.com/image/thumb/PurpleSource211/v4/33/e7/96/33e7962d-7427-ab1c-9a87-2269449603d6/Placeholder.mill/128x128bb-75.webp")

    # 推送行程轨迹图
    PUSH_DRIVE_TRACK: bool = os.getenv("PUSH_DRIVE_TRACK", "true").lower() == "true"

    # 高德地图 API KEY
    AMAP_API_KEY: str = os.getenv("AMAP_API_KEY", "")

    # 百度地图 API KEY
    BAIDU_MAP_API_KEY: str = os.getenv("BAIDU_MAP_API_KEY", "")

    # 车辆 ID（如填写，则指定车辆，不填写或填写 ALL 则全部车辆监测）
    CAR_ID: str = os.getenv("CAR_ID", "ALL")

    # 轮询间隔（秒）
    POLL_INTERVAL: int = int(os.getenv("POLL_INTERVAL", "10"))

    # 行程推送门槛 最小行驶公里数
    MIN_DRIVE_DISTANCE_KM: float = float(os.getenv("MIN_DRIVE_DISTANCE_KM", "1.0"))
    # 行程推送门槛 最小行驶时间（分钟）
    MIN_DRIVE_DURATION_MIN: int = int(os.getenv("MIN_DRIVE_DURATION_MIN", "1"))

    # 时区
    TZ: str = os.getenv("TZ", "Asia/Shanghai")

    def __init__(self):
        self.BATTERY_IMG = {"1":"https://esaimg.cdn1.vip/i/6a0cb0238f3cd_1779216419.png","2":"https://esaimg.cdn1.vip/i/6a0cb11ac29af_1779216666.png","3":"https://esaimg.cdn1.vip/i/6a0cb11ac480d_1779216666.png","4":"https://esaimg.cdn1.vip/i/6a0cb11aca81b_1779216666.png","5":"https://esaimg.cdn1.vip/i/6a0cb11ae5268_1779216666.png","6":"https://esaimg.cdn1.vip/i/6a0cb11ae6681_1779216666.png","7":"https://esaimg.cdn1.vip/i/6a0cb11aecf49_1779216666.png","8":"https://esaimg.cdn1.vip/i/6a0cb11b1366f_1779216667.png","9":"https://esaimg.cdn1.vip/i/6a0cb11b14827_1779216667.png","10":"https://esaimg.cdn1.vip/i/6a0cb11b1b979_1779216667.png","11":"https://esaimg.cdn1.vip/i/6a0cb11b35e39_1779216667.png","12":"https://esaimg.cdn1.vip/i/6a0cb11b37938_1779216667.png","13":"https://esaimg.cdn1.vip/i/6a0cb11b3ddd9_1779216667.png","14":"https://esaimg.cdn1.vip/i/6a0cb11b58fb4_1779216667.png","15":"https://esaimg.cdn1.vip/i/6a0cb11b5a454_1779216667.png","16":"https://esaimg.cdn1.vip/i/6a0cb11b61265_1779216667.png","17":"https://esaimg.cdn1.vip/i/6a0cb11b7b174_1779216667.png","18":"https://esaimg.cdn1.vip/i/6a0cb11b7d7db_1779216667.png","19":"https://esaimg.cdn1.vip/i/6a0cb11b83946_1779216667.png","20":"https://esaimg.cdn1.vip/i/6a0cb11b9e4de_1779216667.png","21":"https://esaimg.cdn1.vip/i/6a0cb11b9fa6d_1779216667.png","22":"https://esaimg.cdn1.vip/i/6a0cb11ba69e7_1779216667.png","23":"https://esaimg.cdn1.vip/i/6a0dc4d05c8b8_1779287248.png","24":"https://esaimg.cdn1.vip/i/6a0dc4d06c47c_1779287248.png","25":"https://esaimg.cdn1.vip/i/6a0dc4d06efba_1779287248.png","26":"https://esaimg.cdn1.vip/i/6a0dc4d07044b_1779287248.png","27":"https://esaimg.cdn1.vip/i/6a0dc4d07b2c0_1779287248.png","28":"https://esaimg.cdn1.vip/i/6a0dc4d07f201_1779287248.png","29":"https://esaimg.cdn1.vip/i/6a0cb11c0de40_1779216668.png","30":"https://esaimg.cdn1.vip/i/6a0cb11c0f285_1779216668.png","31":"https://esaimg.cdn1.vip/i/6a0cb11c1652b_1779216668.png","32":"https://esaimg.cdn1.vip/i/6a0cb11c32798_1779216668.png","33":"https://esaimg.cdn1.vip/i/6a0cb11c33cff_1779216668.png","34":"https://esaimg.cdn1.vip/i/6a0cb11c38806_1779216668.png","35":"https://esaimg.cdn1.vip/i/6a0cb11c56edb_1779216668.png","36":"https://esaimg.cdn1.vip/i/6a0cb11c55e16_1779216668.png","37":"https://esaimg.cdn1.vip/i/6a0cb11c5acb1_1779216668.png","38":"https://esaimg.cdn1.vip/i/6a0cb11c7b309_1779216668.png","39":"https://esaimg.cdn1.vip/i/6a0cb11c7e51a_1779216668.png","40":"https://esaimg.cdn1.vip/i/6a0cb11c7f6c3_1779216668.png","41":"https://esaimg.cdn1.vip/i/6a0cb11c9e3f7_1779216668.png","42":"https://esaimg.cdn1.vip/i/6a0cb11ca44f0_1779216668.png","43":"https://esaimg.cdn1.vip/i/6a0cb11ca8a27_1779216668.png","44":"https://esaimg.cdn1.vip/i/6a0d38cd9f0f1_1779251405.png","45":"https://esaimg.cdn1.vip/i/6a0d38cd9d05c_1779251405.png","46":"https://esaimg.cdn1.vip/i/6a0d38cd9e2a7_1779251405.png","47":"https://esaimg.cdn1.vip/i/6a0d38cdc3f15_1779251405.png","48":"https://esaimg.cdn1.vip/i/6a0d38cdc6139_1779251405.png","49":"https://esaimg.cdn1.vip/i/6a0d38cdc735b_1779251405.png","50":"https://esaimg.cdn1.vip/i/6a0cb11d0d025_1779216669.png","51":"https://esaimg.cdn1.vip/i/6a0d38fb6b091_1779251451.png","52":"https://esaimg.cdn1.vip/i/6a0d38fb4df0a_1779251451.png","53":"https://esaimg.cdn1.vip/i/6a0d38fb4cc37_1779251451.png","54":"https://esaimg.cdn1.vip/i/6a0d38fb47e5b_1779251451.png","55":"https://esaimg.cdn1.vip/i/6a0d38fb25edb_1779251451.png","56":"https://esaimg.cdn1.vip/i/6a0d38fb24cc2_1779251451.png","57":"https://esaimg.cdn1.vip/i/6a0d38fb1c927_1779251451.png","58":"https://esaimg.cdn1.vip/i/6a0d38faebc36_1779251450.png","59":"https://esaimg.cdn1.vip/i/6a0d38faece68_1779251450.png","60":"https://esaimg.cdn1.vip/i/6a0d38faede55_1779251450.png","61":"https://esaimg.cdn1.vip/i/6a0d3900e0139_1779251456.png","62":"https://esaimg.cdn1.vip/i/6a0d3900e112f_1779251456.png","63":"https://esaimg.cdn1.vip/i/6a0d3900def35_1779251456.png","64":"https://esaimg.cdn1.vip/i/6a0d39010df26_1779251457.png","65":"https://esaimg.cdn1.vip/i/6a0d3901113c0_1779251457.png","66":"https://esaimg.cdn1.vip/i/6a0d3901125ca_1779251457.png","67":"https://esaimg.cdn1.vip/i/6a0d390131ab8_1779251457.png","68":"https://esaimg.cdn1.vip/i/6a0d390134f25_1779251457.png","69":"https://esaimg.cdn1.vip/i/6a0d3901365d1_1779251457.png","70":"https://esaimg.cdn1.vip/i/6a0d390155d24_1779251457.png","71":"https://esaimg.cdn1.vip/i/6a0d390791574_1779251463.png","72":"https://esaimg.cdn1.vip/i/6a0d3907905b7_1779251463.png","73":"https://esaimg.cdn1.vip/i/6a0d39078f40e_1779251463.png","74":"https://esaimg.cdn1.vip/i/6a0d3907b4871_1779251463.png","75":"https://esaimg.cdn1.vip/i/6a0d3907b964d_1779251463.png","76":"https://esaimg.cdn1.vip/i/6a0d74ce09585_1779266766.png","77":"https://esaimg.cdn1.vip/i/6a0d74ce0d64b_1779266766.png","78":"https://esaimg.cdn1.vip/i/6a0d74ce0c16a_1779266766.png","79":"https://esaimg.cdn1.vip/i/6a0d74ce1cbdb_1779266766.png","80":"https://esaimg.cdn1.vip/i/6a0d74ce205b3_1779266766.png","81":"https://esaimg.cdn1.vip/i/6a0d74d429ba1_1779266772.png","82":"https://esaimg.cdn1.vip/i/6a0d74d428b41_1779266772.png","83":"https://esaimg.cdn1.vip/i/6a0d74d427a44_1779266772.png","84":"https://esaimg.cdn1.vip/i/6a0d74d43b0a4_1779266772.png","85":"https://esaimg.cdn1.vip/i/6a0d74d43c252_1779266772.png","86":"https://esaimg.cdn1.vip/i/6a0d74d89a9bd_1779266776.png","87":"https://esaimg.cdn1.vip/i/6a0d74d89bc3c_1779266776.png","88":"https://esaimg.cdn1.vip/i/6a0d74d89ce04_1779266776.png","89":"https://esaimg.cdn1.vip/i/6a0d74d8abea2_1779266776.png","90":"https://esaimg.cdn1.vip/i/6a0d74d8ae335_1779266776.png","91":"https://esaimg.cdn1.vip/i/6a0d74de01fc5_1779266782.png","92":"https://esaimg.cdn1.vip/i/6a0d74de00c82_1779266782.png","93":"https://esaimg.cdn1.vip/i/6a0d74de032ec_1779266782.png","94":"https://esaimg.cdn1.vip/i/6a0d74de15ddb_1779266782.png","95":"https://esaimg.cdn1.vip/i/6a0d74de16e91_1779266782.png","96":"https://esaimg.cdn1.vip/i/6a0d74e140f3b_1779266785.png","97":"https://esaimg.cdn1.vip/i/6a0d74e1422a0_1779266785.png","98":"https://esaimg.cdn1.vip/i/6a0d74e143363_1779266785.png","99":"https://esaimg.cdn1.vip/i/6a0d74e152fd9_1779266785.png","100":"https://esaimg.cdn1.vip/i/6a0d74e157527_1779266785.png"}


    @property
    def db_dsn(self) -> str:
        return (
            f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
        )


config = Config()
