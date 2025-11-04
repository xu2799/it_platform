from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import CreateCheckoutSessionView, StripeWebhookView, RegisterView

router = DefaultRouter()
# 1. 课程路由
router.register(r'courses', views.CourseViewSet, basename='course')
# 2. 章节路由
router.register(r'modules', views.ModuleViewSet, basename='module')
# 3. 课时路由
router.register(r'lessons', views.LessonViewSet, basename='lesson')

# 4. 【【【新增】】】: 课程分类路由
router.register(r'categories', views.CategoryViewSet, basename='category')
# 5. 【【【新增】】】: 讲师申请路由
router.register(r'applications', views.InstructorApplicationViewSet, basename='application')


urlpatterns = [
    # 把 router 管理的所有网址包含进来
    path('', include(router.urls)),

    # 用户“我”的网址
    path('users/me/', views.UserView.as_view(), name='user-me'),
    # 支付
    path('checkout/', CreateCheckoutSessionView.as_view(), name='checkout'),
    # Webhook
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    # 注册
    path('register/', RegisterView.as_view(), name='register'),
]