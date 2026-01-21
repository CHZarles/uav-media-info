

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