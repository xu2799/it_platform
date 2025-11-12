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

    def validate_bio(self, value):
        """验证个人简介长度"""
        if value and len(value) > 1000:
            raise serializers.ValidationError("个人简介长度不能超过1000个字符")
        return value


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
    
    def validate_title(self, value):
        """验证课时标题"""
        if not value or not value.strip():
            raise serializers.ValidationError("课时标题不能为空")
        if len(value) > 255:
            raise serializers.ValidationError("课时标题长度不能超过255个字符")
        return value.strip()


class ModuleSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order', 'lessons']
    
    def validate_title(self, value):
        """验证章节标题"""
        if not value or not value.strip():
            raise serializers.ValidationError("章节标题不能为空")
        if len(value) > 255:
            raise serializers.ValidationError("章节标题长度不能超过255个字符")
        return value.strip()


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
            'created_at',
            'instructor',
            'cover_image',
            'category',
            'like_count'
        ]

    def get_like_count(self, obj):
        # 使用已预取的likes关系，避免额外查询
        if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['likes'])
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
        # 使用已预取的likes关系，避免额外查询
        if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
            return len(obj._prefetched_objects_cache['likes'])
        return obj.likes.count()

    def get_is_liked(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            # 使用已预取的likes关系
            if hasattr(obj, '_prefetched_objects_cache') and 'likes' in obj._prefetched_objects_cache:
                return any(like.pk == user.pk for like in obj._prefetched_objects_cache['likes'])
            return obj.likes.filter(pk=user.pk).exists()
        return False

    def get_is_favorited(self, obj):
        user = self.context['request'].user
        if user.is_authenticated:
            # 优化：使用exists()而不是filter().exists()以利用数据库索引
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

    def validate_justification(self, value):
        """验证申请理由"""
        if not value or not value.strip():
            raise serializers.ValidationError("申请理由不能为空")
        if len(value) < 10:
            raise serializers.ValidationError("申请理由不能少于10个字符")
        if len(value) > 2000:
            raise serializers.ValidationError("申请理由长度不能超过2000个字符")
        return value.strip()

    def validate(self, data):
        request = self.context['request']
        if request.user.role != CustomUser.ROLE_STUDENT:
            raise serializers.ValidationError("只有学生才能申请成为讲师")
        if InstructorApplication.objects.filter(user=request.user).exists():
            raise serializers.ValidationError("你已经提交过申请，请勿重复提交")
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
    
    def validate_content(self, value):
        """验证评论内容"""
        if not value or not value.strip():
            raise serializers.ValidationError("评论内容不能为空")
        if len(value) > 2000:
            raise serializers.ValidationError("评论内容长度不能超过2000个字符")
        return value.strip()