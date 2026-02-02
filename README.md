# UAV Media Backend (Drone Stream Server)

一个基于 FastAPI 的“无人机视频流状态 + 录像归档”后端：
- 接收 ZLMediaKit WebHook（上线/断流/录像完成）
- 维护进程内存里的在线状态（`stream_id -> drone_id`）
- 将 MP4 录像事件写入 PostgreSQL（表：`video_recordings`）
- 对外提供业务 API（在线列表、播放地址、录像列表）

> 运行环境：进入 Conda 环境 `conda activate ninja`

---

## 目录结构（核心）
- `app/main.py`：FastAPI 入口，挂载路由 `/hook` 与 `/api`
- `app/api/v1/hooks.py`：ZLM WebHook 接口
- `app/api/v1/streams.py`：业务 API（注册/在线列表/播放地址/录像列表）
- `app/services/drone_service.py`：核心业务逻辑（内存状态、录像入库）
- `app/core/state.py`：进程内存状态（`DRONE_SESSIONS` / `DRONE_ID_MAP`）
- `app/db/models.py`：SQLAlchemy 模型（`VideoRecord`）
- `db/create_user.sql`、`db/init_db.sql`：数据库初始化脚本
- `mock_zlmedia.py`：Mock ZLM（监听 9000，向后端发送 hooks）
- `mock_drone_cli.py`：CLI 模拟注册/推流/断流

---

## 快速开始（本地）

### 1) 安装依赖
```bash
conda activate ninja
pip install -r requirements.txt
```

### 2) 配置环境变量
项目使用 `app/core/config.py` 读取环境变量（支持 `.env`）。

`.env` 示例（根据实际环境修改）：
```ini
DATABASE_URL=postgresql://uav_user:change_me@localhost:5432/uav
ZLM_HOST=http://localhost:9000
ZLM_SECRET=035c73f7-bb6b-4889-a715-d9eb2d1925cc
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

> `ZLM_HOST` 会被用来拼接播放地址：`{ZLM_HOST}/{app}/{stream}.flv`

### 3) 初始化数据库（PostgreSQL 14+）
```bash
# 以 postgres 系统用户执行，避免 peer 认证问题
sudo -u postgres psql -f db/create_user.sql

# 初始化表结构
PGPASSWORD='change_me' psql -h localhost -U uav_user -d uav -f db/init_db.sql
```

### 4) 启动后端
```bash
conda activate ninja
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Mock 全链路验证（推荐）

### 终端 1：启动后端
```bash
conda activate ninja
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 终端 2：启动 Mock ZLM（9000）
```bash
conda activate ninja
python mock_zlmedia.py
```

### 终端 3：执行 CLI 模拟
```bash
conda activate ninja

# 完整流程：注册 -> 通知 ZLM 开始推流
python mock_drone_cli.py --action full --drone-id drone_001 --stream-id s_001

# 模拟断流（会触发 on_stream_changed + on_record_mp4）
python mock_drone_cli.py --action stop --stream-id s_001
```

验证接口：
- 在线列表：`GET http://localhost:8000/api/streams/online`
- 播放地址：`GET http://localhost:8000/api/stream/play-url?id=s_001&type=live`
- 录像列表：`GET http://localhost:8000/api/recordings`

---

## API 清单（以代码为准）

### WebHook（ZLM -> 后端）
- `POST /hook/on_publish`：流上线（注册过的 stream 会标记 Online）
- `POST /hook/on_stream_changed`：流状态变更（`regist=false` 标记 Offline）
- `POST /hook/on_record_mp4`：录像完成（仅对“已注册 stream”入库；未注册会忽略）

### 业务 API（前端/网关 -> 后端）
- `POST /api/stream/register`：设备注册（绑定 `drone_id` 与 `stream_id`）
- `GET /api/streams/online`：在线流列表（来自进程内存）
- `GET /api/stream/play-url?id=...&type=live`：拼接播放地址（当前返回 `.flv`）
- `GET /api/recordings?drone_id=...`：录像列表（PostgreSQL）

---

## CI/CD（GitHub Actions）
- CI：`.github/workflows/ci.yml`（push/PR 自动跑：ruff + pytest；带 Postgres service）
- Docker：`.github/workflows/docker.yml`
  - PR：只构建
  - push 到 `master`/`main` 或打 `v*` tag：构建并推送到 GHCR `ghcr.io/<owner>/<repo>`

---

## 开发（可选）
安装开发依赖：
```bash
conda activate ninja
pip install -r requirements-dev.txt
```

运行测试（需可访问 PostgreSQL，并设置 `DATABASE_URL`）：
```bash
conda activate ninja
python -m pytest -q
```
