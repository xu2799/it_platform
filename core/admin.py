from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    Course,
    Module,
    Lesson,
    Enrollment,
    LessonProgress,
    Category,
    InstructorApplication,
    Comment
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
# 2. 自定义 Category Admin (不变)
# -----------------------------------------------------------------------------
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ['name', 'slug']


# -----------------------------------------------------------------------------
# 3. 自定义 InstructorApplication Admin - 【【【已修复】】】
# -----------------------------------------------------------------------------
@admin.register(InstructorApplication)
class InstructorApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username']
    actions = ['approve_applications', 'reject_applications']

    # 【【【新增：修复Bug】】】
    # 覆盖 save_model 以确保在 "save" 按钮被点击时也触发角色升级
    def save_model(self, request, obj, form, change):
        # 检查状态是否从 "非批准" 变为了 "批准"
        if 'status' in form.changed_data and obj.status == InstructorApplication.STATUS_APPROVED:
            # 升级用户角色
            user = obj.user
            user.role = CustomUser.ROLE_INSTRUCTOR
            user.save()

        super().save_model(request, obj, form, change)

    # 【核心】: 审批动作 (不变)
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
admin.site.register(Category, CategoryAdmin)
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(LessonProgress)
admin.site.register(Comment)
# InstructorApplication 已通过 @admin.register 注册