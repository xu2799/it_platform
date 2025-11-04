from rest_framework import serializers
from .models import CustomUser, Course, Module, Lesson, Category, InstructorApplication


# -----------------------------------------------------------------------------
# 打包器 1: 用户
# -----------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    # (来自之前的修复: 包含 'enrollments' 字段)
    enrollments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'bio', 'role', 'enrollments']
        read_only_fields = ['role', 'username']


# -----------------------------------------------------------------------------
# 【【【新增】】】: 课程分类打包器
# -----------------------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


# -----------------------------------------------------------------------------
# 打包器 2, 3: 课程内容
# -----------------------------------------------------------------------------
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id',
            'module',
            'title',
            'lesson_type',
            'content',
            'video_mp4_file',
            'video_m3u8_url',
            'order'
        ]


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order', 'lessons']


# -----------------------------------------------------------------------------
# 打包器 4: 课程 (公开列表) - 【【已修改】】
# -----------------------------------------------------------------------------
class CourseListSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    # 【【【修改】】】: 添加 category 字段
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'price',
            'created_at',
            'instructor',
            'cover_image',
            'category'  # <-- 【【【修改】】】
        ]


# -----------------------------------------------------------------------------
# 打包器 5: 课程 (完整详情) - 【【已修改】】
# -----------------------------------------------------------------------------
class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    instructor = UserSerializer(read_only=True)
    # 【【【修改】】】: 添加 category 字段
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            'price',
            'created_at',
            'instructor',
            'modules',
            'cover_image',
            'category'  # <-- 【【【修改】】】
        ]


# -----------------------------------------------------------------------------
# 【【【新增】】】: 讲师申请打包器
# -----------------------------------------------------------------------------
class InstructorApplicationSerializer(serializers.ModelSerializer):
    # 在“只读”时 (GET), 嵌套显示申请人信息
    user = UserSerializer(read_only=True)

    class Meta:
        model = InstructorApplication
        fields = ['id', 'user', 'justification', 'status', 'created_at']
        # 'status' 和 'user' 应该是只读的，除非是管理员
        read_only_fields = ['status', 'created_at']

    def validate(self, data):
        # 确保申请人是 'student'
        request = self.context['request']
        if request.user.role != CustomUser.ROLE_STUDENT:
            raise serializers.ValidationError("只有学生才能申请成为讲师。")
        # 确保没有重复申请
        if InstructorApplication.objects.filter(user=request.user).exists():
            raise serializers.ValidationError("你已经提交过申请，请勿重复提交。")
        return data