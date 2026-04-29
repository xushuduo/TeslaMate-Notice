# TeslaMate Notice

基于 [TeslaMate](https://github.com/teslamate-org/teslamate) 的车辆实时通知程序，通过监听 TeslaMate 的 PostgreSQL 数据库与 WebSocket，在行程结束、充电开始/结束、哨兵模式触发时向你的手机推送通知。同时程序还会通过高德地图 API 对地址信息进行修复，解决因 OpenStreetMap 被墙导致地址信息缺失的问题。

---

## 功能

| 功能 | 说明 |
|------|------|
| 🚗 行程通知 | 行程结束后推送里程、耗时、电耗、起终点地址 |
| 🔋 充电通知 | 开始充电 / 充电完成时推送电量、功率、增加续航 |
| 🛡️ 哨兵模式通知 | 检测到哨兵模式录制时推送当前位置 |
| 📍 地址修复 | 通过高德地图 API 将经纬度解析并修复 |
| 📲 多平台推送 | 同时支持 特特管家 和 Bark 两个推送平台 |

---

## 快速部署

### 1. 将服务添加到你现有的 `docker-compose.yml`

```yaml
teslamate-notice:
  image: xushuduo/teslamate-notice:latest
  restart: always
  environment:
    # TeslaMate 地址（同 compose 网络内直接填服务名）
    - TESLAMATE_HOST=teslamate

    # PostgreSQL（与 TeslaMate 共用）
    - DATABASE_HOST=database
    - DATABASE_NAME=teslamate
    - DATABASE_USER=teslamate
    - DATABASE_PASS=password

    # 推送平台（留空则不启用）
    - TETE_PUSH_API_URL=
    - BARK_PUSH_API_URL=

    # 高德地图 API Key（用于地址解析，留空则不解析地址）
    - AMAP_API_KEY=
  depends_on:
    - database
    - teslamate
```

### 2. 启动

```bash
docker compose up -d teslamate-notice
```

### 3. 查看日志

```bash
docker compose logs -f teslamate-notice
```

---

## 环境变量说明

| 变量 | 必填 | 默认值 | 说明 |
|------|------|--------|------|
| `TESLAMATE_HOST` | 是 | `teslamate` | TeslaMate 服务地址 |
| `TESLAMATE_PORT` | 否 | `4000` | TeslaMate 服务端口 |
| `DATABASE_HOST` | 是 | `database` | PostgreSQL 主机名 |
| `DATABASE_PORT` | 否 | `5432` | PostgreSQL 端口 |
| `DATABASE_NAME` | 否 | `teslamate` | 数据库名称 |
| `DATABASE_USER` | 否 | `teslamate` | 数据库用户名 |
| `DATABASE_PASS` | 是 | `password` | 数据库密码 |
| `TETE_PUSH_API_URL` | 否 | — | TETE 推送 URL，留空不启用 |
| `BARK_PUSH_API_URL` | 否 | — | Bark 推送 URL，留空不启用 |
| `AMAP_API_KEY` | 否 | — | 高德地图 API Key，用于地址解析 |
| `POLL_INTERVAL` | 否 | `10` | 数据库轮询间隔（秒） |
| `MIN_DRIVE_DISTANCE_KM` | 否 | `1.0` | 触发行程通知的最小里程（km） |
| `MIN_DRIVE_DURATION_MIN` | 否 | `1` | 触发行程通知的最小时长（分钟） |
| `TZ` | 否 | `Asia/Shanghai` | 时区 |
| `RETRY_COUNT` | 否 | `5` | 推送失败重试次数 |
| `RETRY_INTERVAL` | 否 | `10` | 推送重试间隔（秒） |

---

## 推送API URL 和高德API KEY 说明

### 推送API URL

`TETE_PUSH_API_URL`为[特特管家](https://apps.apple.com/app/id6738431519)的推送功能，API获取流程
- 打开“特特管家“应用，点击右上角“🔔“图标，顶部公告栏“特特管家通知API已开放“，复制API链接
- API链接参考：https://tesla.funtao8.com/tesla/push.php?token=xxxxx

`BARK_PUSH_API_URL`为[Bark](https://apps.apple.com/app/id1403753865)的推送功能，API获取流程
- 打开“Bark“应用，点击最下面“服务器“，复制任意一条链接均可。
- API链接参考：https://api.day.app/xxxxx/

### 高德API KEY
`AMAP_API_KEY`为[高德地图开放平台](https://console.amap.com/dev/key/app)的经纬度逆地理编码功能
- 完成注册高德地图开发平台，并通过账号认证。
- 进入“应用管理“，点击“我的应用“，点击右上角“创建新应用“，应用名称输入“TeslaMateNotice“，应该类型选择“工具“。
- 创建完成应用后，“添加Key“，Key名称输入“逆地理编码“，服务平台为“Web服务“，勾选同意后“提交“。
- Key参考：47x76f1x9cfcx5xdfx15x31xbb57fx8x

---

## 项目结构

```
.
├── app/
│   ├── config.py        # 环境变量配置
│   ├── db.py            # PostgreSQL 查询
│   ├── monitor.py       # 数据库轮询线程
│   ├── ws.py            # TeslaMate WebSocket 订阅线程
│   ├── notifier.py      # TETE / Bark 推送
│   ├── address_fix.py   # 地址修复
│   └── tools.py         # 工具函数
├── main.py              # 程序入口（双线程启动）
├── requirements.txt
└── Dockerfile
```

---

## License

MIT
