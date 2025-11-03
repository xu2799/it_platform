import os
from celery import Celery

# 设置 Django 环境变量, 告诉 Celery 使用哪个设置文件
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'it_platform.settings')

# 创建 Celery 实例
# 'it_platform' 是项目的名字
app = Celery('it_platform')

# 从 Django 的 settings 文件中加载配置 (这样它就会读取我们刚设置的 CELERY_BROKER_URL 等)
app.config_from_object('django.conf:settings', namespace='CELERY')

# 自动发现 Django 应用中的任务
# (这意味着所有应用文件夹里的 tasks.py 文件都会被自动加载)
app.autodiscover_tasks()

# 示例任务 (用于启动测试)
@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')