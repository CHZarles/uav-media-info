# 项目代码框架说明文档

本文档详细说明了 UAV Media Backend 项目的代码结构、各模块功能及核心工作流程。

## 1. 项目结构概览

本项目采用 **分层架构** 设计，实现了接口层、业务逻辑层、数据持久化层的分离。

```plaintext
drone-stream-server/
├── app/
│   ├── main.py              # 程序入口，初始化 FastAPI 应用
│   ├── api/                 # 接口层 (API Controllers)
│   │   └── v1/
│   │       ├── hooks.py     # ZLMediaKit 回调接口 (WebHooks)
│   │       └── streams.py   # 业务查询接口 (前端/无人机调用)
│   ├── core/                # 核心配置与状态
│   │   ├── config.py        # 环境变量配置 (Env, DB URL)
│   │   └── state.py         # 内存全局状态 (DroneSession 管理)
│   ├── db/                  # 数据库层 (ORM)
│   │   ├── base.py          # SQLAlchemy Session 工厂
│   │   └── models.py        # 数据库模型 (VideoRecord)
│   ├── schemas/             # 数据验证层 (Pydantic Models)
│   │   ├── hook_schema.py   # WebHook 入参校验模型
│   │   └── stream_schema.py # 业务接口出入参模型
│   └── services/            # 业务逻辑层 (Service Layer)
│       ├── drone_service.py # 核心业务逻辑 (状态更新、DB写入)
│       └── zlm_service.py   # ZLMediaKit API 调用封装
├── .env                     # 环境变量配置文件
├── requirements.txt         # Python 依赖清单
└── docs/                    # 项目文档
```

---

## 2. 核心模块详解

### 2.1 程序入口 (`app/main.py`)
- 初始化 FastAPI 实例。
- 注册路由 (`app.include_router`)。
- 启动时自动创建数据库表 (`Base.metadata.create_all`)。

### 2.2 接口层 (`app/api/`)
负责接收 HTTP 请求，进行参数校验，然后调用 Service 层处理业务，最后返回 JSON 响应。

- **`v1/hooks.py`**:
    - 处理来自 ZLMediaKit 的 WebHook 事件。
    - `/on_publish`: 流上线通知，调用 Service 更新内存状态。
    - `/on_stream_changed`: 流断开通知，更新对应的在线状态。
    - `/on_record_mp4`: 录制完成通知，将录像记录写入数据库。
- **`v1/streams.py`**:
    - 面向前端或无人机设备的业务 API。
    - `/stream/register`: 无人机设备注册 (DroneID <-> StreamID 绑定)。
    - `/streams/online`: 获取当前在线流列表 (直接查内存)。
    - `/recordings`: 查询历史录像 (查数据库)。

### 2.3 核心配置 (`app/core/`)
- **`config.py`**: 使用 `pydantic-settings` 读取环境变量 (如 `DATABASE_URL`, `ZLM_HOST`)。
- **`state.py`**: 定义并维护全局内存状态。
    - `DRONE_SESSIONS`: 一个字典，存储当前所有流的动态信息 (在线状态、分辨率等)。
    - **设计意图**: 直播状态是瞬时且高频访问的，适合存内存；而录像记录是持久的，适合入库。

### 2.4 数据库层 (`app/db/`)
- **`models.py`**: 定义 SQLAlchemy 模型。目前仅包含 `VideoRecord` 表，用于存储录像文件的物理路径和索引信息。
- **`base.py`**: 提供数据库连接池 (Engine) 和 Session 生成器 (`get_db`)。

### 2.5 业务逻辑层 (`app/services/`)
这是系统的“大脑”，负责具体的逻辑判断。

- **`drone_service.py`**:
    - **`register_drone`**: 建立 DroneID 与 StreamID 的映射。
    - **`handle_publish`**: 处理流上线，更新内存中的 `DroneSession` 状态为 `Online`。
    - **`handle_record_mp4`**: 接收录制文件路径，创建 `VideoRecord` 数据库记录。
- **`zlm_service.py`**:
    - 封装对 ZLMediaKit HTTP API 的调用 (如 `getMediaList`, `close_stream`)。

---

## 3. 核心工作流

### 3.1 设备注册与推流
1. **注册**: 无人机调用 `/api/stream/register`，Server 在内存 `state.DRONE_SESSIONS` 中预创建 Session (Status=Offline)。
2. **推流**: 无人机向 ZLM 推送 RTMP/RTSP 流。
3. **上线回调**: ZLM 调用 `/hook/on_publish`。
4. **状态更新**: `Hooks` 接口调用 `DroneService`，找到对应的 Session，将其标记为 `Online`，并记录流参数。

### 3.2 录像归档
1. **停止推流**: 无人机断开连接，ZLM 结束 MP4 录制。
2. **录制完成回调**: ZLM 调用 `/hook/on_record_mp4`，携带文件路径。
3. **入库**: `Hooks` 接口调用 `DroneService`，向 `video_recordings` 表插入一条新记录。

---

## 4. 快速开始

### 安装依赖
```bash
pip install -r requirements.txt
```

### 配置环境
确保 `.env` 文件已正确配置数据库和 ZLM 地址：
```ini
DATABASE_URL=postgresql://user:pass@localhost:5432/uav
ZLM_HOST=http://localhost:8000
```

### 启动服务
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
