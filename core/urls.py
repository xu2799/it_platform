from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CreateCheckoutSessionView, StripeWebhookView, RegisterView # <-- 导入 RegisterView
# ...

router = DefaultRouter()
# 1. 课程路由 (不变)
router.register(r'courses', views.CourseViewSet, basename='course')

# 【这是你新加的】:
# 2. 章节路由
router.register(r'modules', views.ModuleViewSet, basename='module')
# 3. 课时路由
router.register(r'lessons', views.LessonViewSet, basename='lesson')

urlpatterns = [
    # 把 router 管理的所有网址 (courses/, modules/, lessons/) 包含进来
    path('', include(router.urls)),

    # 用户“我”的网址 (不变)
    path('users/me/', views.UserView.as_view(), name='user-me'),
    path('checkout/', CreateCheckoutSessionView.as_view(), name='checkout'),
    # 【这是你新加的】: Stripe Webhook 路由
    # Stripe 会 POST 请求到这个地址
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    # 用户注册 API 路由
    path('register/', RegisterView.as_view(), name='register'),
]