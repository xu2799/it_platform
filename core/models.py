from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.utils.text import slugify  # <-- 导入 slugify


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

    def __str__(self):
        return self.username


# -----------------------------------------------------------------------------
# 【【【已修复】】】: 课程分类模型 (Category)
# -----------------------------------------------------------------------------
class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="分类名称")
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        help_text="用于URL的短标签, 例如 'python'",
        allow_unicode=True  # <-- 【【【修复 1: 允许字段存储中文字符】】】
    )

    class Meta:
        verbose_name_plural = "Categories"  # 修复 admin 中的复数显示

    def save(self, *args, **kwargs):
        if not self.slug:
            # 【【【修复 2: 告诉 slugify 函数保留中文字符】】】
            self.slug = slugify(self.name, allow_unicode=True)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


# -----------------------------------------------------------------------------
# 蓝图 2: 课程模型 (Course) - (不变)
# -----------------------------------------------------------------------------
class Course(models.Model):
    title = models.CharField(max_length=255, verbose_name="课程标题")
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
        verbose_name="课程分类"
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
# 蓝图 3: 章节模型 (Module) - (不变)
# -----------------------------------------------------------------------------
class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules', verbose_name="所属课程")
    title = models.CharField(max_length=255, verbose_name="章节标题")
    order = models.PositiveIntegerField(default=0, verbose_name="章节顺序")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} - {self.title}"


# -----------------------------------------------------------------------------
# 蓝图 4: 课时模型 (Lesson) - (不变)
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
    video_mp4_file = models.FileField(
        upload_to='lesson_videos_mp4/',
        null=True,
        blank=True,
        verbose_name="上传的MP4原文件"
    )
    video_m3u8_url = models.URLField(blank=True, null=True, verbose_name="HLS视频URL")
    content = models.TextField(blank=True, verbose_name="文本内容")
    order = models.PositiveIntegerField(default=0, verbose_name="课时顺序")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


# -----------------------------------------------------------------------------
# 蓝图 5: 注册 (购买) 模型 (Enrollment) - (不变)
# -----------------------------------------------------------------------------
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments',
                                verbose_name="学生")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments', verbose_name="课程")
    enrolled_at = models.DateTimeField(auto_now_add=True, verbose_name="注册时间")

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} 注册了 {self.course.title}"


# -----------------------------------------------------------------------------
# 蓝图 6: 学习进度模型 (LessonProgress) - (不变)
# -----------------------------------------------------------------------------
class LessonProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress',
                                verbose_name="学生")
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress', verbose_name="课时")
    is_completed = models.BooleanField(default=False, verbose_name="是否完成")

    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f"{self.student.username} - {self.lesson.title}"


# -----------------------------------------------------------------------------
# 蓝图 7: 讲师申请模型 (InstructorApplication) - (不变)
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

    # 申请人 (一个学生只能申请一次)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='application',
        verbose_name="申请人"
    )
    # 申请理由
    justification = models.TextField(verbose_name="申请理由")
    # 申请状态
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
        verbose_name="申请状态"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="申请时间")

    def __str__(self):
        return f"{self.user.username} 的讲师申请 ({self.get_status_display()})"