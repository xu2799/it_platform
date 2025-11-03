"""
Django settings for it_platform project.
"""

from pathlib import Path
import os # <-- 确保导入 os, 用于读取环境变量

# BASE_DIR 指向 '.../MyProjects/it_platform'
BASE_DIR = Path(__file__).resolve().parent.parent


# --- 1. 核心安全设置 ---

# 【【警告】】: 请从您之前的文件中，把您的 SECRET_KEY 复制粘贴回这里！
# （例如：SECRET_KEY = 'django-insecure-_#w=dw-...'）
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-YOUR_SECRET_KEY_GOES_HERE')

# 开发模式
DEBUG = True

# 允许您的前端主机访问
ALLOWED_HOSTS = ['localhost', '127.0.0.1']


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
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# --- 11. DRF (REST Framework) ---
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ]
}

# --- 12. Celery 和 Redis (异步任务) ---
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']


# --- 13. Stripe 支付配置 ---
# 【【警告】】: 请从您之前的文件中，把您的3个 Stripe 密钥复制粘贴回这里！
STRIPE_PUBLISHABLE_KEY = "pk_test_51SOy8PRr0O6RH57lgGmy3JjC6nqC7Ul3ozcuX60IH7b2kmsB89xJugNlivPWSLCJivE7FpteVsXK5VQ33UZuCnDc000rik5PRH"
STRIPE_SECRET_KEY = "sk_test_51SOy8PRr0O6RH57lffl1niV4FjjwRzH1UlDuRs9axN57H3KYXFEZ6UTh9TZA0emKRugtcjZbVKV57zgmGROKROor00k95TP7P0"
STRIPE_WEBHOOK_SECRET = "whsec_...PASTE_YOUR_KEY_HERE..."

STRIPE_SUCCESS_URL = 'http://localhost:5173/payment/success'
STRIPE_CANCEL_URL = 'http://localhost:5173/payment/cancel'


# --- 14. 文件上传大小限制 ---
FILE_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 52428800  # 50MB