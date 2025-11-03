from rest_framework import serializers
from .models import CustomUser, Course, Module, Lesson

# ... UserSerializer (不变) ...

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'bio', 'role']
        read_only_fields = ['role', 'username']

# -----------------------------------------------------------------------------
# 打包器 2, 3, 4: 课程内容打包器
# -----------------------------------------------------------------------------

# 【修复 1: 课时打包器】:
# 我们删除了原来的 read_only=True, 让讲师可以创建/更新课时
class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = [
            'id',
            'module',
            'title',
            'lesson_type',
            'content',
            'video_mp4_file',  # <--- 新增
            'video_m3u8_url',
            'order'
        ]
# 【修复 2: 章节打包器】:
# 我们删除了原来的 read_only=True, 让讲师可以创建/更新章节
class ModuleSerializer(serializers.ModelSerializer):
    # 【关键修复】: 嵌套字段必须是 read_only=True
    #   我们必须让 Lessons 字段是只读的, 否则讲师在创建章节时,
    #   API 会要求他把所有课时的内容也一次性交上来, 这不合理
    lessons = LessonSerializer(many=True, read_only=True)

    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'order', 'lessons'] # <-- 增加 'course' 字段

# 【修复 3: 课程打包器】:
# 我们删除了原来的 read_only=True, 让讲师可以创建/更新课程
class CourseSerializer(serializers.ModelSerializer):
    # 【关键修复】: 嵌套字段必须是 read_only=True
    modules = ModuleSerializer(many=True, read_only=True)
    instructor = UserSerializer(read_only=True)

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
            'cover_image'  # <--- 【【【这就是修复的地方】】】
        ]