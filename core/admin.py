from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    Course,
    Module,
    Lesson,
    Enrollment,
    LessonProgress
)

# -----------------------------------------------------------------------------
# 1. 自定义 CustomUser 在 admin 中的显示
# -----------------------------------------------------------------------------
# 我们需要告诉 admin, "role" 和 "bio" 字段也需要显示
class CustomUserAdmin(UserAdmin):
    # UserAdmin.fieldsets 是 Django 原本就定义好的一堆字段
    # 我们要做的就是找到 "Personal info" 那一组, 把我们的新字段加进去
    fieldsets = UserAdmin.fieldsets + (
        ('自定义字段', {'fields': ('role', 'bio')}),
    )
    # 也要把新字段加到 "add_fieldsets", 这样 "创建用户" 时也能看到
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('自定义字段', {'fields': ('role', 'bio')}),
    )
    # 也要在 "list_display" (列表页) 中添加, 这样能一眼看到
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'role']

# -----------------------------------------------------------------------------
# 2. 【核心】把你的所有模型“注册”到 admin 后台
# -----------------------------------------------------------------------------

# 告诉 admin: "请使用我们上面定义的 CustomUserAdmin 规则来管理 CustomUser"
admin.site.register(CustomUser, CustomUserAdmin)

# 告诉 admin: "请用默认的样式来管理这些模型"
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(LessonProgress)