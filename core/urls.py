from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import RegisterView

router = DefaultRouter()
# 1. 课程路由
router.register(r'courses', views.CourseViewSet, basename='course')
# 2. 章节路由
router.register(r'modules', views.ModuleViewSet, basename='module')
# 3. 课时路由
router.register(r'lessons', views.LessonViewSet, basename='lesson')
# 4. 课程分类路由
router.register(r'categories', views.CategoryViewSet, basename='category')
# 5. 讲师申请路由
router.register(r'applications', views.InstructorApplicationViewSet, basename='application')
# 6. 评论路由
router.register(r'comments', views.CommentViewSet, basename='comment')

urlpatterns = [
    # 把 router 管理的所有网址包含进来
    path('', include(router.urls)),

    # 用户“我”的网址
    path('users/me/', views.UserView.as_view(), name='user-me'),

    # 讲师 "我的课程" 网址
    path('instructor/courses/', views.InstructorCourseListView.as_view(), name='instructor-courses'),

    # --- 【【【已删除】】】 ---
    # 点赞 API 已被移除
    # 收藏 API 已被移除
    # 收藏列表 API 已被移除

    # 注册
    path('register/', RegisterView.as_view(), name='register'),
]