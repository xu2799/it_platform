"""
it_platform URL Configuration
"""
from django.contrib import admin
from django.urls import path, include

# 1. 用于 DRF 的 Token 认证
from rest_framework.authtoken.views import obtain_auth_token

# 2. 【【【这就是关键修复】】】
#    导入 static() 和 settings,
#    用于在“开发模式”下提供“媒体文件”（如课程封面）服务
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # A. Django 自带的后台管理页面
    path('admin/', admin.site.urls),

    # B. DRF 为“可浏览 API” 提供的登录/退出按钮
    path('api-auth/', include('rest_framework.urls')),

    # C. 为“程序化”登录 (如 Vue.js) 提供的 Token 获取 API
    path('api/token-auth/', obtain_auth_token, name='api_token_auth'),

    # D. 【核心】: 将所有 /api/ 开头的 URL 都转交给 'core.urls' 文件去处理
    path('api/', include('core.urls')),
]

# --- 媒体文件服务 ---
# 【【【这就是关键修复】】】
# 仅在“开发模式” (DEBUG=True) 下，
# 告诉 Django 如何提供用户上传的媒体文件 (MEDIA_URL 和 MEDIA_ROOT)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)