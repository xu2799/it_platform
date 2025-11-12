"""
Django settings for it_platform project.
"""

from pathlib import Path
import os # <-- 确保导入 os, 用于读取环境变量

# BASE_DIR 指向 '.../MyProjects/it_platform'
BASE_DIR = Path(__file__).resolve().parent.parent


# --- 1. 核心安全设置 ---

# 安全配置：从环境变量读取SECRET_KEY，生产环境必须设置
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-YOUR_SECRET_KEY_GOES_HERE')

# 开发模式：生产环境必须设置为False
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# 允许的主机：生产环境需要配置实际域名
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# --- 2. 应用程序定义 ---
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

    # --- 我们自己的应用 ---
    'core.apps.CoreConfig',
]

# --- 3. 中间件 ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',

    # 【CORS 修复】: 必须放在 CommonMiddleware 的“上方”
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
        'DIRS': [], # 我们是前后端分离, Django 不需要渲染 templates
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


# --- 4. 数据库 ---
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# --- 5. 密码验证 (保持默认) ---
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# --- 6. 国际化 ---
LANGUAGE_CODE = 'zh-hans' # 中文
TIME_ZONE = 'Asia/Shanghai' # 上海时间
USE_I18N = True
USE_TZ = True


# ==================================================================
#
#           【【【 我们的项目核心配置 】】】
#
# ==================================================================

# --- 7. 静态文件 (用于 Admin 后台) ---
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles_build' # 部署时使用

# --- 8. 媒体文件 (用于用户上传的封面图/视频) ---
# 【【【 这是修复“封面不显示”的第一部分 】】】
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# --- 9. 自定义用户模型 ---
AUTH_USER_MODEL = 'core.CustomUser'


# --- 10. 跨域许可 (CORS) ---
# 开发环境允许的源
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# 从环境变量读取额外的允许源（生产环境使用）
if os.getenv('CORS_ALLOWED_ORIGINS'):
    CORS_ALLOWED_ORIGINS.extend(os.getenv('CORS_ALLOWED_ORIGINS').split(','))

# 安全配置：生产环境应该限制更严格的CORS设置
CORS_ALLOW_CREDENTIALS = True


# --- 11. DRF (REST Framework) ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # 分页配置：避免返回过多数据
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    # 异常处理
    'EXCEPTION_HANDLER': 'rest_framework.views.exception_handler',
}

# --- 12. Celery 和 Redis (异步任务) ---
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']


# --- 13. Stripe 支付配置 ---
# 【【【修改】】】: 所有 Stripe 密钥已被移除


# --- 14. 文件上传大小限制 ---
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB

# --- 15. 安全中间件配置 ---
if not DEBUG:
    # 生产环境安全配置
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# --- 16. 日志配置 ---
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}