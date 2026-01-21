

## Mock 验证全链路

现在你拥有了三个文件：
1.  **`server.py`** ：业务后端，监听 8000。
2.  **`mock_zlm.py`** (之前的代码)：Mock ZLM，监听 9000。
3.  **`mock_drone_cli.py`** (之前的代码)：CLI 工具，用于发指令。

**操作步骤：**

1.  **终端 1 (启动后端)**:
    ```bash
    python server.py
    ```

2.  **终端 2 (启动 Mock ZLM)**:
    ```bash
    python mock_zlm.py
    ```

3.  **终端 3 (执行 CLI 模拟)**:
    
    *   **完整流程 (注册 -> 上线)**:
        ```bash
        python mock_drone_cli.py --action full --stream-id s_001
        ```
        *观察终端 1，你会看到 "设备已注册" 和 "📡 [Hook] 收到推流请求... 🟢 Online"*。

    *   **查看在线列表 (浏览器)**:
        访问 `http://localhost:8000/api/streams/online`，你会看到状态是 `Online`。

    *   **模拟断流 (录像)**:
        ```bash
        python mock_drone_cli.py --action stop --stream-id s_001
        ```
        *观察终端 1，你会看到 "🔌 [Hook] 流断开... 🔴 Offline" 和 "💾 [Hook] 录像完成"*。

    *   **查看录像列表 (浏览器)**:
        访问 `http://localhost:8000/api/recordings`，你会看到刚才生成的模拟录像数据。


## 初始化数据库

```sql
# -u postgres: 告诉 sudo 以系统用户 "postgres" 的身份运行后面的命令
# 这样系统用户就是 postgres，数据库用户也是 postgres，Peer 认证就会通过
sudo -u postgres psql -f create_user.sql


# PGPASSWORD=... : 临时指定密码环境变量，避免交互式输入
# -h localhost   : 强制走 TCP/IP 网络协议，触发密码认证（而不是 Peer）
# -U uav_user : 指定使用刚才创建的业务用户
PGPASSWORD='change_me' psql -h localhost -U uav_user -d uav -f init_db.sql
```


## V0
- [] 设备注册与推流上线流程
- [] 前端获取直播地址与观看流程
- [] 断流与录像归档流程
- [] 历史录像回放流程