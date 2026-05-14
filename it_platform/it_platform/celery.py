import os
from celery import Celery

# 为 celery 设置默认的 django settings 模块
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'it_platform.settings')

# 创建 celery 实例
app = Celery('it_platform')

# 从 Django 的 settings.py 中读取配置，配置项以 CELERY_ 开头
app.config_from_object('django.conf:settings', namespace='CELERY')

# 让 Celery 自动去所有已注册的 Django app 中寻找 @shared_task 任务
app.autodiscover_tasks()