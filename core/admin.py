from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    Course,
    Module,
    Lesson,
    Enrollment,
    LessonProgress,
    Category,  # <-- 【【【新增】】】
    InstructorApplication  # <-- 【【【新增】】】
)


# -----------------------------------------------------------------------------
# 1. 自定义 CustomUser Admin (不变)
# -----------------------------------------------------------------------------
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('自定义字段', {'fields': ('role', 'bio')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('自定义字段', {'fields': ('role', 'bio')}),
    )
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'role']


# -----------------------------------------------------------------------------
# 2. 自定义 Category Admin (让 slug 自动填充)
# -----------------------------------------------------------------------------
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'slug']


# -----------------------------------------------------------------------------
# 3. 自定义 InstructorApplication Admin (用于审批)
# -----------------------------------------------------------------------------
@admin.register(InstructorApplication)
class InstructorApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username']
    actions = ['approve_applications', 'reject_applications']

    # 【核心】: 审批动作
    def approve_applications(self, request, queryset):
        for application in queryset.filter(status=InstructorApplication.STATUS_PENDING):
            application.status = InstructorApplication.STATUS_APPROVED
            application.save()

            # 将用户角色升级为讲师
            user = application.user
            user.role = CustomUser.ROLE_INSTRUCTOR
            user.save()

    approve_applications.short_description = "批准所选申请并设为讲师"

    def reject_applications(self, request, queryset):
        queryset.update(status=InstructorApplication.STATUS_REJECTED)

    reject_applications.short_description = "拒绝所选申请"


# -----------------------------------------------------------------------------
# 4. 注册所有模型
# -----------------------------------------------------------------------------
admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(Category, CategoryAdmin)  # <-- 【【【新增】】】
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(LessonProgress)
# InstructorApplication 已通过 @admin.register 注册