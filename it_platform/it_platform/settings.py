"""
Django settings for it_platform project.
"""

from pathlib import Path
from decouple import config
import os

# BASE_DIR 指向项目根目录
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================================================================
# 1. 核心安全设置
# ==============================================================================

try:
    from decouple import config
    # 使用环境变量，如果不存在则使用默认值
    SECRET_KEY = config('DJANGO_SECRET_KEY', default='django-insecure-local-dev-key-for-testing-only')
    DEBUG = config('DEBUG', default=True, cast=bool)
    ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='*').split(',')
except ImportError:
    # 如果未安装 python-decouple，使用默认值（开发环境）
    SECRET_KEY = 'django-insecure-local-dev-key-for-testing-only'
    DEBUG = True
    ALLOWED_HOSTS = ['*']


# ==============================================================================
# 2. 应用程序定义
# ==============================================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # --- 第三方应用 ---
    'corsheaders',              # 1. CORS 跨域许可
    'rest_framework',           # 2. DRF 核心
    'rest_framework.authtoken', # 3. Token 认证

    # --- 本地应用 ---
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # 【关键】CORS 中间件必须放在 CommonMiddleware 之前
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'it_platform.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'it_platform.wsgi.application'


# ==============================================================================
# 3. 数据库配置
# ==============================================================================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'it_platform_db',
        'USER': 'root',
        'PASSWORD': '123456',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    }
}


# ==============================================================================
# 4. 密码验证策略 (开发环境简化版)
# ==============================================================================

# 【修改】仅保留最小长度限制，方便测试 (例如允许 '123456')
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
]


# ==============================================================================
# 5. 国际化与时区
# ==============================================================================

LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True


# ==============================================================================
# 6. 静态文件与媒体文件 (核心配置)
# ==============================================================================

# 静态文件 (Admin后台样式等)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_build'

# 【关键】媒体文件 (用户上传的头像、封面、视频)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==============================================================================
# 7. 自定义用户模型
# ==============================================================================

AUTH_USER_MODEL = 'core.CustomUser'


# ==============================================================================
# 8. 跨域设置 (CORS)
# ==============================================================================

# 允许前端地址
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 允许携带凭证 (Cookie等)
CORS_ALLOW_CREDENTIALS = True


# ==============================================================================
# 9. DRF (REST Framework) 配置
# ==============================================================================

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # 分页配置
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # 异常处理
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
    # 【新增】请求频率限制
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',   # 匿名用户每小时100次请求
        'user': '1000/hour',  # 认证用户每小时1000次请求
    }
}


# ==============================================================================
# 10. Celery 异步任务配置
# ==============================================================================

try:
    from decouple import config
    CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
    CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
except ImportError:
    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
    CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'

CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']


# ==============================================================================
# 11. 缓存配置 (新增)
# ==============================================================================

# 使用内存缓存（不需要Redis），简化配置
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
        'OPTIONS': {
            'MAX_ENTRIES': 1000
        }
    }
}

# 如果需要使用Redis缓存，请先确保Redis服务运行，然后使用以下配置：
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': 'redis://127.0.0.1:6379/1',
#         'KEY_PREFIX': 'it_platform',
#         'TIMEOUT': 300,
#     }
# }


# ==============================================================================
# 11. 其他配置
# ==============================================================================

# 文件上传大小限制 (50MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800

# 默认主键类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 日志配置 (可选，用于调试)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# DeepSeek API 配置
DEEPSEEK_API_KEY = config('DEEPSEEK_API_KEY', default='sk-b5bfffe705754c96b859538b80efbfc6')