--- START OF FILE create_user.sql ---

-- UAV Media Backend - Database User Setup
-- Target: PostgreSQL 14+
-- Usage (psql):
--   Edit the variables in the DO block (v_db_name/v_db_user/v_db_pass),
--   then run: psql -U postgres -d postgres -f db/create_user.sql

DO $$
DECLARE
    -- 自定义变量: 媒体/录像服务专用库
    v_db_name text := 'uav';
    v_db_user text := 'uav_user';
    v_db_pass text := 'change_me';
BEGIN
    -- 1) Create role (user) if it does not exist
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = v_db_user) THEN
        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', v_db_user, v_db_pass);
    END IF;

    -- 2) (Database creation is done outside DO; see below)
END
$$;

-- 2) Create database if it does not exist (psql-only trick)
SELECT format('CREATE DATABASE %I OWNER %I', v_db_name, v_db_user)
FROM (VALUES ('uav'::text, 'uav_user'::text)) AS v(v_db_name, v_db_user)
WHERE NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = v.v_db_name)
\gexec

-- 3) Grants
GRANT CONNECT ON DATABASE uav TO uav_user;
-- 如果需要该用户有建表权限（通常 Owner 自带，但显式授权更稳妥）:
-- ALTER USER uav_user CREATEDB;