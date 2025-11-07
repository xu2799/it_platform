from rest_framework import serializers
from .models import (
    CustomUser, Course, Module, Lesson, Category,
    InstructorApplication, Comment
)


# -----------------------------------------------------------------------------
# 打包器 1: 用户
# -----------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    enrollments = serializers.PrimaryKeyRelatedField(many=True, read_only=True)
    favorited_courses = serializers.PrimaryKeyRelatedField(many=True, read_only=True)

    class Meta:
        model = CustomUser
        fields = [
            'id', 'username', 'email', 'bio', 'role',
            'enrollments',
            'favorited_courses'
        ]
        read_only_fields = ['role', 'username']


# -----------------------------------------------------------------------------
# 打包器 2: 课程分类 (不变)
# -----------------------------------------------------------------------------
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


# -----------------------------------------------------------------------------
# 打包器 3, 4: 课程内容 (不变)
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
# 打包器 5: 课程 (公开列表) - 【【【已修改】】】
# -----------------------------------------------------------------------------
class CourseListSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    like_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            # 'price', # <-- 【【【已移除】】】
            'created_at',
            'instructor',
            'cover_image',
            'category',
            'like_count'
        ]

    def get_like_count(self, obj):
        return obj.likes.count()


# -----------------------------------------------------------------------------
# 打包器 6: 课程 (完整详情) - 【【【已修改】】】
# -----------------------------------------------------------------------------
class CourseDetailSerializer(serializers.ModelSerializer):
    modules = ModuleSerializer(many=True, read_only=True)
    instructor = UserSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    like_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_favorited = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            'id',
            'title',
            'description',
            # 'price', # <-- 【【【已移除】】】
            'created_at',
            'instructor',
            'modules',
            'cover_image',
            'category',
            'like_count',
            'is_liked',
            'is_favorited'
        ]

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return obj.likes.filter(pk=user.pk).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            return user.favorited_courses.filter(pk=obj.pk).exists()
        return False


# -----------------------------------------------------------------------------
# 打包器 7: 讲师申请 (不变)
# -----------------------------------------------------------------------------
class InstructorApplicationSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = InstructorApplication
        fields = ['id', 'user', 'justification', 'status', 'created_at']
        read_only_fields = ['status', 'created_at']

    def validate(self, data):
        request = self.context['request']
        if request.user.role != CustomUser.ROLE_STUDENT:
            raise serializers.ValidationError("只有学生才能申请成为讲师。")
        if InstructorApplication.objects.filter(user=request.user).exists():
            raise serializers.ValidationError("你已经提交过申请，请勿重复提交。")
        return data


# -----------------------------------------------------------------------------
# 打包器 8: 评论 (不变)
# -----------------------------------------------------------------------------
class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'lesson', 'content', 'created_at']
        read_only_fields = ['user', 'created_at']