--- START OF FILE init_db.sql ---

-- UAV Media Backend - Database Initialization
-- Target: PostgreSQL 14+
-- Context: Storage for "on_record_mp4" events.

-- Cleanup old indexes if re-running (Idempotency)
-- DROP INDEX IF EXISTS idx_video_recordings_drone_time;
-- DROP INDEX IF EXISTS idx_video_recordings_stream;
-- DROP INDEX IF EXISTS idx_video_recordings_start_time;

BEGIN;

-- 1) Core table: video_recordings
CREATE TABLE IF NOT EXISTS video_recordings (
    record_id       BIGSERIAL PRIMARY KEY,
    
    -- 标识信息
    stream_id       VARCHAR(128) NOT NULL, -- 流ID (如: drone_01_session_x)
    drone_id        VARCHAR(64) NOT NULL,  -- 无人机ID
    
    -- 文件路径信息
    file_path       TEXT NOT NULL,         -- 物理磁盘路径 (/data/video/xxx.mp4)
    -- play_url        TEXT NULL,             -- HTTP播放地址 (http://ip:port/xxx.mp4)
    
    -- -- 时间信息 (推荐存储 Unix Timestamp，单位: 秒或毫秒，需与代码约定)
    -- start_time      BIGINT NOT NULL,       -- 录制开始时间戳
    -- end_time        BIGINT NOT NULL,       -- 录制结束时间戳
    -- duration_sec    NUMERIC(10, 3) NOT NULL DEFAULT 0, -- 视频时长(秒)，保留3位小数
    
    -- 元数据 (File Meta)
    -- width           INTEGER NULL,          -- 分辨率宽
    -- height          INTEGER NULL,          -- 分辨率高
    -- file_size_bytes BIGINT NOT NULL DEFAULT 0, -- 文件大小(字节)
    
    -- 系统字段
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2) Indexes
-- 场景：查询某架无人机的历史回放列表（按时间倒序）
-- CREATE INDEX IF NOT EXISTS idx_video_recordings_drone_time
--     ON video_recordings (drone_id, start_time DESC);

-- -- 场景：根据流ID精确查找某次推流的录像
-- CREATE INDEX IF NOT EXISTS idx_video_recordings_stream
--     ON video_recordings (stream_id);

-- -- 场景：按时间范围筛选所有录像
-- CREATE INDEX IF NOT EXISTS idx_video_recordings_start_time
--     ON video_recordings (start_time);

COMMIT;