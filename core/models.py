# core/models.py (正确、干净的版本)
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.text import slugify


# -----------------------------------------------------------------------------
# 蓝图 1: 自定义用户模型 (CustomUser)
# -----------------------------------------------------------------------------
class CustomUser(AbstractUser):
    ROLE_STUDENT = 'student'
    ROLE_INSTRUCTOR = 'instructor'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_STUDENT, '学生'),
        (ROLE_INSTRUCTOR, '讲师'),
        (ROLE_ADMIN, '管理员'),
    ]
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_STUDENT,
        verbose_name="用户角色"
    )
    bio = models.TextField(blank=True, verbose_name="个人简介")

    # 收藏 功能
    favorited_courses = models.ManyToManyField(
        'Course',  # 使用字符串 'Course' 避免 import 顺序问题
        blank=True,
        related_name='favorited_by',
        verbose_name="收藏的课程"
    )

    def __str__(self):
        return self.username


# -----------------------------------------------------------------------------
# 蓝图 2: 课程分类模型 (Category)
# -----------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="分类名称")
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="用于URL的短标签, 例如 'python'",
        allow_unicode=True
    )

    class Meta:
        verbose_name_plural = "Categories"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# -----------------------------------------------------------------------------
# 蓝图 3: 课程模型 (Course) - 【【【已修复】】】
# -----------------------------------------------------------------------------
class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name="课程标题", db_index=True)
    description = models.TextField(verbose_name="课程描述")
    cover_image = models.ImageField(
        upload_to='course_covers/',
        null=True,
        blank=True,
        verbose_name="课程封面图"
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
        verbose_name="课程分类",
        db_index=True
    )
    instructor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='courses_taught',
        verbose_name="授课讲师",
        db_index=True
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    # (price 字段已彻底移除, 重复的 Meta 和 likes 也已移除)

    # 点赞功能
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_courses',
        blank=True,
        verbose_name="点赞用户"
    )

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['category', '-created_at']),
            models.Index(fields=['instructor', '-created_at']),
        ]

    def __str__(self):
        return self.title


# -----------------------------------------------------------------------------
# 蓝图 4: 章节模型 (Module)
# -----------------------------------------------------------------------------
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name="所属课程", db_index=True)
    title = models.CharField(max_length=255, verbose_name="章节标题")
    order = models.PositiveIntegerField(default=0, verbose_name="章节顺序", db_index=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['course', 'order']),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# -----------------------------------------------------------------------------
# 蓝图 5: 课时模型 (Lesson)
# -----------------------------------------------------------------------------
class Lesson(models.Model):
    LESSON_VIDEO = 'video'
    LESSON_TEXT = 'text'
    LESSON_TYPE_CHOICES = [
        (LESSON_VIDEO, '视频'),
        (LESSON_TEXT, '文本'),
    ]
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons', verbose_name="所属章节", db_index=True)
    title = models.CharField(max_length=255, verbose_name="课时标题")
    lesson_type = models.CharField(max_length=10, choices=LESSON_TYPE_CHOICES, default=LESSON_TEXT,
                                   verbose_name="课时类型", db_index=True)
    video_mp4_file = models.FileField(
        upload_to='lesson_videos_mp4/',
        null=True,
        blank=True,
        verbose_name="上传的MP4原文件"
    )
    video_m3u8_url = models.URLField(blank=True, null=True, verbose_name="HLS视频URL")
    content = models.TextField(blank=True, verbose_name="文本内容")
    order = models.PositiveIntegerField(default=0, verbose_name="课时顺序", db_index=True)

    class Meta:
        ordering = ['order']
        indexes = [
            models.Index(fields=['module', 'order']),
            models.Index(fields=['lesson_type']),
        ]

    def __str__(self):
        return self.title


# -----------------------------------------------------------------------------
# 蓝图 6: 注册 (购买) 模型 (Enrollment)
# -----------------------------------------------------------------------------
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments',
                                verbose_name="学生", db_index=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name="课程", db_index=True)
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="注册时间", db_index=True)

    class Meta:
        unique_together = ('student', 'course')
        indexes = [
            models.Index(fields=['student', '-enrolled_at']),
            models.Index(fields=['course', '-enrolled_at']),
        ]

    def __str__(self):
        return f"{self.student.username} 注册了 {self.course.title}"


# -----------------------------------------------------------------------------
# 蓝图 7: 学习进度模型 (LessonProgress)
# -----------------------------------------------------------------------------
class LessonProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress',
                                verbose_name="学生", db_index=True)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress', verbose_name="课时", db_index=True)
    is_completed = models.BooleanField(default=False, verbose_name="是否完成", db_index=True)

    class Meta:
        unique_together = ('student', 'lesson')
        indexes = [
            models.Index(fields=['student', 'is_completed']),
            models.Index(fields=['lesson', 'is_completed']),
        ]

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"


# -----------------------------------------------------------------------------
# 蓝图 8: 讲师申请模型 (InstructorApplication)
# -----------------------------------------------------------------------------
class InstructorApplication(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_CHOICES = [
        (STATUS_PENDING, '待处理'),
        (STATUS_APPROVED, '已批准'),
        (STATUS_REJECTED, '已拒绝'),
    ]
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='application',
        verbose_name="申请人"
    )
    justification = models.TextField(verbose_name="申请理由")
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="申请状态"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")

    def __str__(self):
        return f"{self.user.username} 的讲师申请 ({self.get_status_display()})"


# -----------------------------------------------------------------------------
# 蓝图 9: 评论模型 (Comment)
# -----------------------------------------------------------------------------
class Comment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='comments', verbose_name="所属课时", db_index=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='comments',
                             verbose_name="评论用户", db_index=True)
    content = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评论时间", db_index=True)

    class Meta:
        ordering = ['-created_at']  # 按时间倒序
        indexes = [
            models.Index(fields=['lesson', '-created_at']),
            models.Index(fields=['user', '-created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} 对 {self.lesson.title} 的评论"