# Theta Terminal 设置指南

## 🎯 目标

设置 Theta Terminal 本地服务器，为增量数据同步提供数据源。

## 📋 前置条件

- Java 21 或更高版本
- Theta Data 账户（免费或付费）

---

## 步骤 1: 安装 Java 21

### Ubuntu/Debian

```bash
sudo apt update
sudo apt install openjdk-21-jdk openjdk-21-jre

# 验证安装
java -version
# 应该显示: openjdk version "21.x.x" 或更高
```

### macOS

```bash
brew install openjdk@21

# 添加到 PATH
echo 'export PATH="/usr/local/opt/openjdk@21/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 验证安装
java -version
```

### Windows

1. 下载 OpenJDK 21: https://jdk.java.net/21/
2. 解压到 `C:\Program Files\Java\jdk-21`
3. 添加到 PATH 环境变量
4. 验证: `java -version`

---

## 步骤 2: 下载 Theta Terminal

1. 访问 https://thetadata.net
2. 注册/登录账户
3. 下载 **Theta Terminal** JAR 文件
4. 保存到项目目录或单独文件夹

```bash
# 推荐目录结构
/home/user/theta/
├── ThetaTerminalv3.jar
└── creds.txt  # 凭证文件（自动生成）
```

---

## 步骤 3: 启动 Theta Terminal

### 首次启动

```bash
cd /path/to/theta
java -jar ThetaTerminalv3.jar
```

**首次启动会发生**：
1. 自动下载最新版本
2. 创建配置文件
3. 要求输入登录凭证
4. 连接到 Theta Data 服务器
5. 启动本地 HTTP 服务器（端口 25503）

### 后台运行

```bash
# Linux/macOS
nohup java -jar ThetaTerminalv3.jar > terminal.log 2>&1 &

# 记录 PID
echo $! > terminal.pid

# 停止 Terminal
kill $(cat terminal.pid)
```

### 使用 systemd（推荐生产环境）

创建服务文件 `/etc/systemd/system/theta-terminal.service`：

```ini
[Unit]
Description=Theta Terminal Data Server
After=network.target

[Service]
Type=simple
User=adt
WorkingDirectory=/home/adt/theta
ExecStart=/usr/bin/java -jar ThetaTerminalv3.jar
Restart=on-failure
RestartSec=10
StandardOutput=append:/home/adt/theta/terminal.log
StandardError=append:/home/adt/theta/terminal.log

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl start theta-terminal
sudo systemctl enable theta-terminal  # 开机自启

# 查看状态
sudo systemctl status theta-terminal

# 查看日志
tail -f /home/adt/theta/terminal.log
```

---

## 步骤 4: 验证 Terminal 运行

### 检查端口

```bash
# Linux/macOS
lsof -i :25503

# 或
ss -tuln | grep 25503

# 应该看到:
# tcp   LISTEN  0  50  *:25503  *:*
```

### 测试 API 连接

```bash
# 测试连接
curl http://localhost:25503/v3/stock/list/symbols

# 应该返回股票列表（CSV 格式）
```

### 使用 Python 测试

```bash
cd /home/adt/project/agentic_trading
python scripts/test_theta_terminal.py
```

**预期输出**：

```
======================================================================
🔍 Theta Terminal 连接测试
======================================================================

步骤 1: 连接到 Theta Terminal...
✅ 客户端初始化成功

步骤 2: 获取 SPY OHLC 快照...
✅ OHLC 数据:
   Open:   $590.50
   High:   $592.30
   Low:    $589.80
   Close:  $591.20
   Volume: 12,345,678

步骤 3: 获取 AAPL 报价快照...
✅ 报价数据:
   Bid:    $175.20 x 100
   Ask:    $175.25 x 100
   Mid:    $175.23
   Volume: 5,234,567

步骤 4: 批量获取数据...
✅ SPY   : $  591.20  (Vol: 12,345,678)
✅ QQQ   : $  505.80  (Vol: 8,456,123)
✅ AAPL  : $  175.23  (Vol: 5,234,567)
✅ NVDA  : $  142.50  (Vol: 15,678,234)

======================================================================
🎉 测试完成！
======================================================================

✅ Theta Terminal 连接正常，可以开始同步数据
```

---

## 步骤 5: 配置增量同步

### 更新 .env 文件

```bash
# .env 文件中已有配置（无需修改）
THETA_TERMINAL_HOST=localhost
THETA_TERMINAL_PORT=25503
```

### 测试单次同步

```bash
python scripts/sync_with_rest_api.py --once
```

### 设置每10分钟自动同步

**方法 A: Cron 任务**

```bash
crontab -e

# 添加：
*/10 * * * * cd /home/adt/project/agentic_trading && /usr/bin/python3 scripts/sync_with_rest_api.py --once >> logs/sync.log 2>&1
```

**方法 B: 守护进程**

```bash
nohup python scripts/sync_with_rest_api.py --interval 10 > logs/sync.log 2>&1 &
echo $! > logs/sync.pid
```

---

## 故障排查

### 问题 1: Terminal 无法启动

**症状**：执行 `java -jar ThetaTerminalv3.jar` 后立即退出

**解决**：

```bash
# 检查 Java 版本
java -version
# 必须是 21 或更高

# 查看错误日志
tail -f terminal.log

# 确保有足够权限
chmod +x ThetaTerminalv3.jar
```

### 问题 2: 端口已被占用

**症状**：`Address already in use: bind`

**解决**：

```bash
# 查找占用端口的进程
lsof -i :25503

# 杀死进程
kill -9 <PID>

# 或更改 Terminal 端口（修改配置文件）
```

### 问题 3: 连接被拒绝

**症状**：`Connection refused` 或 `406 Client Error`

**解决**：

```bash
# 1. 确认 Terminal 正在运行
ps aux | grep ThetaTerminal

# 2. 检查端口是否开放
curl http://localhost:25503/v3/stock/list/symbols

# 3. 查看 Terminal 日志
tail -f terminal.log

# 4. 重启 Terminal
kill $(cat terminal.pid)
java -jar ThetaTerminalv3.jar
```

### 问题 4: 认证失败

**症状**：`Authentication failed`

**解决**：

```bash
# 删除旧凭证
rm creds.txt

# 重新启动 Terminal（会提示输入凭证）
java -jar ThetaTerminalv3.jar
```

---

## API 端点参考

Terminal 提供以下主要端点：

### 股票数据

```bash
# 快照 OHLC
GET http://localhost:25503/v3/stock/snapshot/ohlc?symbol=AAPL

# 快照报价
GET http://localhost:25503/v3/stock/snapshot/quote?symbol=AAPL

# 历史 OHLC
GET http://localhost:25503/v3/stock/hist/ohlc?symbol=AAPL&start_date=20250101&end_date=20250120

# 股票列表
GET http://localhost:25503/v3/stock/list/symbols
```

### 期权数据

```bash
# 期权链到期日
GET http://localhost:25503/v3/option/list/expirations?symbol=AAPL

# 期权链行权价
GET http://localhost:25503/v3/option/list/strikes?symbol=AAPL&expiration=20250221

# 期权快照
GET http://localhost:25503/v3/option/snapshot/quote?symbol=AAPL&expiration=20250221&strike=175&right=C
```

---

## 性能优化

### 1. 增加 Java 堆内存

```bash
java -Xmx4G -jar ThetaTerminalv3.jar
```

### 2. 启用数据缓存

Terminal 会自动缓存数据，无需额外配置。

### 3. 网络优化

```bash
# 确保本地环回接口正常
ping localhost

# 检查延迟
curl -w "@-" -o /dev/null -s http://localhost:25503/v3/stock/list/symbols << 'EOF'
time_total: %{time_total}s
EOF
```

---

## 总结

完成以上步骤后，你将拥有：

✅ 本地运行的 Theta Terminal（端口 25503）
✅ 实时市场数据访问
✅ 每10分钟自动增量同步
✅ 可靠的数据持久化

**下一步**：

```bash
# 1. 启动 Terminal
java -jar ThetaTerminalv3.jar

# 2. 测试连接
python scripts/test_theta_terminal.py

# 3. 运行一次同步
python scripts/sync_with_rest_api.py --once

# 4. 设置定时任务
crontab -e
# 添加: */10 * * * * cd /path && python scripts/sync_with_rest_api.py --once
```

🎉 完成！现在你有了一个完整的市场数据管道！
