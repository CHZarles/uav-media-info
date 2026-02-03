

> ref: https://rcn29iascsr0.feishu.cn/wiki/UGxswf4UlifXrWkqIMicsVAEn2e?fromScene=spaceOverview
## API 开发
**后端服务需要实现的完整接口清单**，分为两类：**WebHook 接收接口（入站）** 和 **业务 API 接口（出站）**。



#### 1. WebHook (供 ZLM 调用)

| 路径 | 方法 | 必须性 | 用途 | 逻辑要点 |
| --- | --- | --- | --- | --- |
| `/hook/on_publish` | POST | **必须** | 流上线 | 校验 `app` 名，关联 `stream_id` 到无人机设备 |
| **`/hook/on_stream_changed`** | POST | **必须** | **流断开** | 判断 `regist=false`，将设备状态置为“离线” |
| `/hook/on_record_mp4` | POST | **必须** | 录制完成 | 接收 `file_path`，存入数据库 |

#### 2. 业务 API (供前端/上云网关调用)

| 路径 | 方法 | 用途 | 备注 |
| --- | --- | --- | --- |
| `/api/stream/register` | POST | 设备注册 | 接收 Drone ID，建立 `stream_id` 与设备的映射关系 (存 Redis， v0 先用进程内存) |
| `/api/streams/online` | GET | 在线列表 | **优先查 Redis 缓存(v0 先用进程内存)**，兜底查 ZLM API (减少对 ZLM 的 HTTP 请求压力) |
| `/api/recordings` | GET | 录像列表 | 查数据库 |

## 存储设计

### 1. 内存存储（极速响应 / 易失性数据）

**对象：** 设备状态、直播元数据。

* **存储内容：** * **设备映射：** `stream_id` 与无人机 SN、名称、机型信息的绑定关系。
* **实时状态：** 当前是否正在推流（Online/Offline）。
* **实时参数：** ZLM 在线流的分辨率、码率、帧率。


* **数据来源：** `/api/stream/register`（预注册）、`on_publish`（上线）、`on_stream_changed`（下线）。
* **特点：** 读写极快，服务重启即重置（可通过重新拉取 ZLM 列表恢复部分状态）。
> 后期用中间间 缓存 信息
---

### 2. 数据库存储（持久化 / 资产数据）

**对象：** 录像文件记录（唯一需要落盘的表）。

* **存储内容（1 张表）：**
* `stream_id`：标识属于哪台飞机。
* `file_path / url`：视频文件的物理路径与 HTTP 播放地址。
* `time_info`：开始时间、结束时间、视频时长。
* `file_meta`：分辨率、文件大小。


* **数据来源：** `on_record_mp4`（录制完成回调）。
* **特点：** 保证服务重启后，历史回放记录不丢失。

---

### 3. 文件系统存储（流媒体原始数据）

**对象：** MP4 录像文件。

* **存储路径：** 由 ZLMediaKit 指定的磁盘路径。
* **管理方式：** 后端数据库只记录其“路径索引”，不存储二进制内容。



##  时序图

### 核心实体说明
*   **无人机/上云API**: 视频源端。
*   **ZLMediaKit**: 流媒体服务器（核心），负责推流、分发、录制。
*   **网关服务 (原入口服务)**: 负责接收 ZLM 的 WebHook 和无人机的注册请求。
*   **处理服务**: 业务逻辑核心，维护**内存状态**。
*   **操作服务**: 面向前端的 API 接口层。
*   **数据库**: 仅存储录像文件记录。
*   **前端底座**: 用户界面。

---

### 1. 设备注册与推流上线流程 (Device Register & Go Live)

此流程描述设备如何告知后端它的存在，以及 ZLM 如何通知后端流已上线。

*   **内存变化**: 建立 `stream_id` 到 `DroneInfo` 的映射，更新流状态为 `Online`。
*   **数据库变化**: 无。

```mermaid
sequenceDiagram
    autonumber
    participant Drone as 上云API(无人机)
    participant ZLM as ZLMediaKit
    participant Gateway as 网关服务(入口)
    participant Process as 处理服务(内存状态)

    Note over Drone, Process: 阶段一：设备预注册 (建立映射)
    Drone->>Gateway: POST /api/stream/register (DroneID, stream_id)
    Gateway->>Process: 转发注册数据
    activate Process
    Process->>Process: 【内存操作】<br/>1. 创建/更新 DroneSession 对象<br/>2. 绑定 stream_id <-> DroneID<br/>3. 标记 status = Offline (等待推流)
    Process-->>Gateway: 注册成功
    deactivate Process
    Gateway-->>Drone: 200 OK

    Note over Drone, Process: 阶段二：推流上线 (ZLM回调)
    Drone->>ZLM: RTMP/RTSP 推流 (stream_id)
    ZLM->>Gateway: POST /hook/on_publish (app, stream_id, param...)
    Gateway->>Process: 转发流上线事件
    activate Process
    Process->>Process: 校验 app 名称
    Process->>Process: 【内存操作】<br/>1. 根据 stream_id 查找 DroneSession<br/>2. 更新 status = Online<br/>3. 更新流元数据(分辨率/码率)
    Process-->>Gateway: 鉴权通过 (code: 0)
    deactivate Process
    Gateway-->>ZLM: 200 OK (允许推流)
```

---

### 2. 前端获取直播地址与观看流程 (Live Playback)

此流程描述前端如何查询在线设备并获取播放地址。

*   **内存变化**: 读取在线列表，读取流状态。
*   **数据库变化**: 无。
*   **兜底策略**: 如果内存中查不到流信息，尝试调用 ZLM API 确认（可选）。

```mermaid
sequenceDiagram
    autonumber
    participant Frontend as 前端底座
    participant Operation as 操作服务
    participant Process as 处理服务(内存状态)
    participant ZLM as ZLMediaKit

    Note over Frontend, ZLM: 场景：获取在线设备列表
    Frontend->>Operation: GET /api/streams/online
    Operation->>Process: 请求在线设备数据
    activate Process
    Process->>Process: 【内存读取】<br/>遍历 DroneSession 列表<br/>筛选 status == Online 的设备
    alt 内存中无数据 (兜底策略)
        Process->>ZLM: GET /index/api/getMediaList (可选)
        ZLM-->>Process: 返回实际流列表
        Process->>Process: 【内存同步】重建内存状态
    end
    Process-->>Operation: 返回在线设备列表 (含 play_url)
    deactivate Process
    Operation-->>Frontend: JSON List
    
    Frontend->>ZLM: 使用 play_url 请求播放（WebRTC/FLV）
    ZLM-->>Frontend: 视频流数据
```

---

### 3. 断流与录像归档流程 (Stream End & Archiving)

这是最关键的流程，涉及状态清理和数据持久化。

*   **内存变化**: 更新流状态为 `Offline`。
*   **数据库变化**: **新增**一条录像记录（文件路径、时长等）。

```mermaid
sequenceDiagram
    autonumber
    participant Drone as 上云API(无人机)
    participant ZLM as ZLMediaKit
    participant Gateway as 网关服务(入口)
    participant Process as 处理服务(内存状态)
    participant DB as 数据库

    Note over Drone, DB: 阶段一：流断开 (修改状态)
    Drone->>ZLM: 停止推流 / 意外断开
    ZLM->>Gateway: POST /hook/on_stream_changed (regist=false)
    Gateway->>Process: 转发断流事件
    activate Process
    Process->>Process: 【内存操作】<br/>1. 查找对应 stream_id<br/>2. 更新 status = Offline<br/>(保留设备映射，不删除对象)
    Process-->>Gateway: 处理完成
    deactivate Process
    Gateway-->>ZLM: 200 OK

    Note over Drone, DB: 阶段二：录制完成 (数据落盘)
    ZLM->>ZLM: 关闭 MP4 文件句柄 (生成文件)
    ZLM->>Gateway: POST /hook/on_record_mp4 (file_path, time, size...)
    Gateway->>Process: 转发录制完成事件
    activate Process
    Process->>Process: 解析 file_path 和时间信息
    Process->>DB: INSERT INTO video_records (...)
    activate DB
    DB-->>Process: 写入成功
    deactivate DB
    Process->>Process: (可选) Log: 录像已归档
    Process-->>Gateway: 处理完成
    deactivate Process
    Gateway-->>ZLM: 200 OK
```

---

### 4. 历史录像回放流程 (History Playback)

此流程完全依赖数据库，不涉及内存中的实时状态。

*   **内存变化**: 无。
*   **数据库变化**: 读取录像记录。

```mermaid
sequenceDiagram
    autonumber
    participant Frontend as 前端底座
    participant Operation as 操作服务
    participant Process as 处理服务
    participant DB as 数据库
    participant ZLM as ZLMediaKit

    Frontend->>Operation: GET /api/recordings?drone_id=xxx&date=...
    Operation->>Process: 查询录像记录
    Process->>DB: SELECT * FROM video_records WHERE ...
    activate DB
    DB-->>Process: 返回结果集 (Path, Time)
    deactivate DB
    
    Process->>Process: 格式化数据<br/>拼接静态文件访问 URL (指向ZLM http服务器)
    Process-->>Operation: 录像列表
    Operation-->>Frontend: JSON List (含播放URL)

    Frontend->>ZLM: 请求 MP4 文件 (HTTP Range)
    ZLM-->>Frontend: 视频流文件
```
