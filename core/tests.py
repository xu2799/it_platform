# core/tests.py
from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from .models import CustomUser, Course, Category, InstructorApplication


class CoreAPITests(APITestCase):

    def setUp(self):
        """
        在每个测试运行前，设置好所需的用户和数据
        """
        # 1. 创建不同角色的用户
        self.student_user = CustomUser.objects.create_user(
            username='student',
            password='password123',
            role=CustomUser.ROLE_STUDENT
        )

        self.instructor_user = CustomUser.objects.create_user(
            username='instructor',
            password='password123',
            role=CustomUser.ROLE_INSTRUCTOR
        )

        self.admin_user = CustomUser.objects.create_user(
            username='admin',
            password='password123',
            role=CustomUser.ROLE_ADMIN,
            is_staff=True,
            is_superuser=True
        )

        # 2. 创建一个课程分类用于测试
        self.category = Category.objects.create(name="Python 开发", slug="python")

        # 3. 定义课程 API URL
        self.courses_url = reverse('course-list')  # 对应 /api/courses/

    def test_student_cannot_create_course(self):
        """
        改进点 1: 测试学生用户没有权限创建课程 (应该返回 403 Forbidden)
        """
        # 强制使用学生身份登录
        self.client.force_authenticate(user=self.student_user)

        course_data = {
            'title': '学生试图创建的课程',
            'description': '这不应该成功',
            'category': self.category.id
        }

        response = self.client.post(self.courses_url, course_data, format='json')

        # 验证是否返回 403 (Forbidden)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Course.objects.count(), 0)  # 确保数据库中没有创建课程

    def test_instructor_can_create_course(self):
        """
        改进点 2: 测试讲师用户有权限创建课程 (应该返回 201 Created)
        """
        # 强制使用讲师身份登录
        self.client.force_authenticate(user=self.instructor_user)

        course_data = {
            'title': '讲师的课程',
            'description': '这应该会成功',
            'category': self.category.id
        }

        response = self.client.post(self.courses_url, course_data, format='json')

        # 验证是否返回 201 (Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Course.objects.count(), 1)  # 确保数据库中已创建课程
        self.assertEqual(Course.objects.get().title, '讲师的课程')

    def test_admin_approve_application_upgrades_role(self):
        """
        改进点 3: 测试管理员批准申请时，是否自动将学生角色提升为讲师
        """
        # 1. 为学生创建一个待处理的申请
        application = InstructorApplication.objects.create(
            user=self.student_user,
            justification="我想成为讲师"
        )
        self.assertEqual(self.student_user.role, CustomUser.ROLE_STUDENT)  # 确认初始角色

        # 2. 强制使用管理员身份登录
        self.client.force_authenticate(user=self.admin_user)

        # 3. 准备 PATCH 请求的数据
        approval_data = {'status': InstructorApplication.STATUS_APPROVED}

        # 获取该申请的详情 URL
        application_detail_url = reverse('application-detail', kwargs={'pk': application.id})

        # 4. 发送批准请求
        response = self.client.patch(application_detail_url, approval_data, format='json')

        # 5. 验证结果
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 6. 【核心验证】: 刷新数据库中的学生对象，检查其角色是否已更新
        self.student_user.refresh_from_db()
        self.assertEqual(self.student_user.role, CustomUser.ROLE_INSTRUCTOR)