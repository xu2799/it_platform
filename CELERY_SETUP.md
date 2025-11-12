# Celery Worker 设置指南

## 问题说明

如果视频上传后一直显示"视频正在处理中"，通常是因为 **Celery Worker 没有运行**。

Celery 是用于处理异步任务（如视频转码）的框架。当视频上传后，系统会将视频处理任务添加到队列中，但只有在 Celery Worker 运行时，这些任务才会被执行。

## 解决步骤

### 1. 确保 Redis 正在运行

Celery 使用 Redis 作为消息代理。首先需要启动 Redis：

#### Windows:
```bash
# 如果使用 WSL (推荐)
wsl redis-server

# 或者使用 Docker
docker run -d -p 6379:6379 redis:latest
```

#### Linux/Mac:
```bash
# 启动 Redis 服务
redis-server

# 或者使用 systemd (Linux)
sudo systemctl start redis
```

### 2. 启动 Celery Worker

在项目根目录（`it_platform` 目录）下，打开新的终端窗口，运行：

```bash
# 激活虚拟环境（如果使用）
# source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate     # Windows

# 启动 Celery Worker
celery -A it_platform worker --loglevel=info
```

如果看到类似以下输出，说明 Celery Worker 已成功启动：

```
[2024-01-01 10:00:00,000: INFO/MainProcess] Connected to redis://127.0.0.1:6379/0
[2024-01-01 10:00:00,000: INFO/MainProcess] mingle: searching for neighbors
[2024-01-01 10:00:00,000: INFO/MainProcess] mingle: all alone
[2024-01-01 10:00:00,000: INFO/MainProcess] celery@hostname ready.
```

### 3. 验证 Celery Worker 是否正常工作

上传一个视频，然后查看 Celery Worker 的日志输出。你应该看到类似以下的消息：

```
[2024-01-01 10:00:00,000: INFO/ForkPoolWorker-1] --- [任务启动] 正在处理 Lesson ID: 1 的视频 ---
[2024-01-01 10:00:10,000: INFO/ForkPoolWorker-1] --- [任务完成] Lesson ID: 1 视频处理成功! URL已更新。 ---
```

### 4. 使用 Celery Beat（可选，用于定时任务）

如果项目中有定时任务，还需要启动 Celery Beat：

```bash
celery -A it_platform beat --loglevel=info
```

## 开发环境快速启动脚本

### Windows (start_celery.bat)
```batch
@echo off
echo Starting Redis...
start "Redis" wsl redis-server

echo Waiting for Redis to start...
timeout /t 3

echo Starting Celery Worker...
celery -A it_platform worker --loglevel=info

pause
```

### Linux/Mac (start_celery.sh)
```bash
#!/bin/bash

echo "Starting Redis..."
redis-server &

echo "Waiting for Redis to start..."
sleep 3

echo "Starting Celery Worker..."
celery -A it_platform worker --loglevel=info
```

## 常见问题

### 问题1: 连接 Redis 失败
```
Error: [Errno 111] Connection refused
```
**解决方案**: 确保 Redis 正在运行。检查 Redis 是否在 6379 端口监听。

### 问题2: 任务没有执行
**解决方案**: 
1. 检查 Celery Worker 是否正在运行
2. 查看 Celery Worker 的日志输出
3. 检查 Django 日志文件是否有错误信息

### 问题3: 视频处理任务失败
**解决方案**: 
1. 查看 Celery Worker 的日志输出
2. 检查视频文件是否存在
3. 检查文件权限

## 生产环境部署

在生产环境中，建议使用进程管理器（如 systemd、supervisor）来管理 Celery Worker：

### systemd 服务示例 (celery-worker.service)
```ini
[Unit]
Description=Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=www-data
Group=www-data
WorkingDirectory=/path/to/it_platform
ExecStart=/path/to/venv/bin/celery -A it_platform worker --loglevel=info --detach
ExecStop=/bin/kill -s TERM $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

## 监控 Celery 任务

### 使用 Flower（可选）
Flower 是 Celery 的 Web 监控工具：

```bash
pip install flower
celery -A it_platform flower
```

然后访问 http://localhost:5555 查看任务状态。

## 注意事项

1. **Celery Worker 必须与 Django 项目在同一环境中运行**
2. **确保 Redis 服务始终运行**
3. **在生产环境中，使用进程管理器来确保 Celery Worker 自动重启**
4. **定期检查 Celery Worker 的日志，及时发现和解决问题**





