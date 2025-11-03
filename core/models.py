from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# -----------------------------------------------------------------------------
# 蓝图 1: 自定义用户模型 (CustomUser)
# -----------------------------------------------------------------------------
# 你的文档要求：我们需要区分 "学生" 和 "讲师"
# 我们通过继承 AbstractUser 来使用 Django 内置的强大用户系统
# 并添加我们自己的 "role" (角色) 字段
# -----------------------------------------------------------------------------
class CustomUser(AbstractUser):
    # 定义角色的常量
    ROLE_STUDENT = 'student'
    ROLE_INSTRUCTOR = 'instructor'
    ROLE_ADMIN = 'admin'

    # (常量, 页面上显示的名字)
    ROLE_CHOICES = [
        (ROLE_STUDENT, '学生'),
        (ROLE_INSTRUCTOR, '讲师'),
        (ROLE_ADMIN, '管理员'),
    ]

    # 我们新增的 "role" 字段
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        verbose_name="用户角色"
    )

    # 我们新增的 "bio" 字段 (个人简介)
    bio = models.TextField(blank=True, verbose_name="个人简介")

    # 告诉 Django 这个类是用来干什么的
    def __str__(self):
        return self.username


# -----------------------------------------------------------------------------
# 蓝图 2: 课程模型 (Course)
# -----------------------------------------------------------------------------
class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name="课程标题")
    description = models.TextField(verbose_name="课程描述")

    # 【新增】: 封面图字段
    # upload_to='course_covers/' 会将文件存储在你的 MEDIA_ROOT/course_covers/ 文件夹下
    cover_image = models.ImageField(
        upload_to='course_covers/',
        null=True,
        blank=True,
        verbose_name="课程封面图"
    )

    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses_taught',
        verbose_name="授课讲师"
    )

    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="价格")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


# -----------------------------------------------------------------------------
# 蓝图 3: 章节模型 (Module)
# -----------------------------------------------------------------------------
# 一门课程 (Course) 包含多个章节 (Module)
# -----------------------------------------------------------------------------
class Module(models.Model):
    # on_delete=models.CASCADE: 级联删除。如果课程被删了，它下面的所有章节也自动被删除。
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name="所属课程")
    title = models.CharField(max_length=255, verbose_name="章节标题")
    order = models.PositiveIntegerField(default=0, verbose_name="章节顺序")  # 用于排序

    class Meta:
        ordering = ['order']  # 默认按 order 字段排序

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# -----------------------------------------------------------------------------
# 蓝图 4: 课时模型 (Lesson)
# -----------------------------------------------------------------------------
# 一个章节 (Module) 包含多个课时 (Lesson)
# -----------------------------------------------------------------------------
class Lesson(models.Model):
    LESSON_VIDEO = 'video'
    LESSON_TEXT = 'text'
    LESSON_TYPE_CHOICES = [
        (LESSON_VIDEO, '视频'),
        (LESSON_TEXT, '文本'),
    ]

    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name="所属章节")
    title = models.CharField(max_length=255, verbose_name="课时标题")
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES, default=LESSON_TEXT,
                                   verbose_name="课时类型")

    # 【新增】: 真正存储上传的 MP4 文件
    video_mp4_file = models.FileField(
        upload_to='lesson_videos_mp4/',
        null=True,
        blank=True,
        verbose_name="上传的MP4原文件"
    )

    # 【核心】视频流 URL (Celery 稍后会填充这个)
    video_m3u8_url = models.URLField(blank=True, null=True, verbose_name="HLS视频URL")

    content = models.TextField(blank=True, verbose_name="文本内容")
    order = models.PositiveIntegerField(default=0, verbose_name="课时顺序")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


# -----------------------------------------------------------------------------
# 蓝图 5: 注册 (购买) 模型 (Enrollment)
# -----------------------------------------------------------------------------
# 记录哪个学生 (Student) 购买了哪门课 (Course)
# -----------------------------------------------------------------------------
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments',
                                verbose_name="学生")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name="课程")
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")

    class Meta:
        # 联合唯一: 确保一个学生对一门课只能注册一次
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} 注册了 {self.course.title}"


# -----------------------------------------------------------------------------
# 蓝图 6: 学习进度模型 (LessonProgress)
# -----------------------------------------------------------------------------
# 【核心】记录哪个学生 (Student) 完成了哪个课时 (Lesson) (你的文档要求)
# -----------------------------------------------------------------------------
class LessonProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress',
                                verbose_name="学生")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress', verbose_name="课时")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")

    class Meta:
        # 联合唯一: 确保一个学生对一个课时只有一条进度记录
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"