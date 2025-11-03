from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import Course, CustomUser, Module, Lesson, Enrollment
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, BasePermission
from .serializers import (
    CourseSerializer, UserSerializer, ModuleSerializer, LessonSerializer
)
from .tasks import process_video_upload
import stripe
from django.conf import settings
from rest_framework.views import APIView

# 【【【 1. 导入文件解析器 (关键) 】】】
from rest_framework.parsers import MultiPartParser, FormParser


# -----------------------------------------------------------------
# 权限: 讲师和管理员
# -----------------------------------------------------------------
class IsInstructorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]


# -----------------------------------------------------------------
# 课程“视图集合”
# -----------------------------------------------------------------
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    # 【【【 2. 指定解析器 (修复) 】】】
    # 告诉这个 ViewSet, 它需要准备好接收“表单数据” (FormData)
    parser_classes = [MultiPartParser, FormParser]

    # 【【【 3. 修复权限 】】】
    def get_permissions(self):
        if self.action == 'create':
            # 只有讲师/管理员才能创建
            return [IsInstructorOrAdmin()]
        # 查看(GET)等其他操作, 任何人都可以
        return [permissions.IsAuthenticatedOrReadOnly()]

    # 【【【 4. 自定义 create 方法 (核心修复) 】】】
    def create(self, request, *args, **kwargs):
        # 检查权限 (必须是讲师/管理员)
        if not request.user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]:
            return Response(
                {"detail": "只有讲师或管理员才能创建课程。"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 从 request.data 中手动获取所有数据
        title = request.data.get('title')
        description = request.data.get('description')
        price = request.data.get('price')
        cover_image_file = request.data.get('cover_image')  # <-- 这就是图片文件

        if not title or not description or not price:
            return Response(
                {"detail": "缺少标题、描述或价格"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 手动创建课程对象
        try:
            course = Course.objects.create(
                title=title,
                description=description,
                price=price,
                instructor=request.user,
                cover_image=cover_image_file  # <-- 将文件对象直接赋值给 ImageField
            )

            # 使用序列化器打包新创建的课程数据并返回给前端
            serializer = self.get_serializer(course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response(
                {"detail": f"创建课程失败: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )

    # (我们重写了 create, 不再需要这个默认的 perform_create)
    # def perform_create(self, serializer):
    #     ...


# -----------------------------------------------------------------
# 章节“视图集合”
# -----------------------------------------------------------------
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsInstructorOrAdmin]


# -----------------------------------------------------------------
# 课时“视图集合” (异步上传)
# -----------------------------------------------------------------
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer

    # 【【【 5. 为 Lesson 添加解析器 (修复) 】】】
    parser_classes = [MultiPartParser, FormParser]

    # (你原有的 create 方法是正确的, 我们保留它)
    def create(self, request, *args, **kwargs):
        self.check_permissions(request)

        lesson_title = request.data.get('title')
        module_id = request.data.get('module')
        uploaded_file = request.data.get('video_file')

        if not uploaded_file or not lesson_title or not module_id:
            return Response(
                {"detail": "缺少文件、标题或章节ID"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            module = Module.objects.get(pk=module_id)

            lesson = Lesson.objects.create(
                module=module,
                title=lesson_title,
                lesson_type=Lesson.LESSON_TEXT,
                content="视频正在处理中...",
                video_mp4_file=uploaded_file
            )
        except Module.DoesNotExist:
            return Response({"detail": "章节不存在"}, status=status.HTTP_400_BAD_REQUEST)

        process_video_upload.delay(lesson.id, lesson.video_mp4_file.path)

        serializer = self.get_serializer(lesson)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# -----------------------------------------------------------------
# 用户“我”视图 (保持不变)
# -----------------------------------------------------------------
class UserView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# -----------------------------------------------------------------
# 【 Stripe 支付 API 】 (保持不变)
# -----------------------------------------------------------------
class CreateCheckoutSessionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        course_id = request.data.get('course_id')
        if not course_id:
            return Response({'detail': '缺少课程 ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'detail': '课程不存在'}, status=status.HTTP_404_NOT_FOUND)
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({'detail': '你已购买此课程'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': 'cny',
                        'product_data': {
                            'name': course.title[:128],
                            'description': course.description[:500],
                        },
                        'unit_amount': int(course.price * 100),
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=settings.STRIPE_SUCCESS_URL + '?session_id={CHECKOUT_SESSION_ID}&course_id=' + str(
                    course.id),
                cancel_url=settings.STRIPE_CANCEL_URL,
                metadata={
                    'course_id': course.id,
                    'user_id': request.user.id
                }
            )
            return Response({
                'url': checkout_session.url,
                'session_id': checkout_session.id
            })
        except stripe.error.StripeError as e:
            return Response({'detail': f'Stripe API 错误: {e.user_message or e.code or e.json_body}'},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'detail': f'内部服务器错误: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# 【 用户注册 API 】 (保持不变)
# -----------------------------------------------------------------
class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role', CustomUser.ROLE_STUDENT)
        if not username or not password:
            return Response({'detail': '用户名和密码不能为空。'}, status=status.HTTP_400_BAD_REQUEST)
        if CustomUser.objects.filter(username=username).exists():
            return Response({'detail': '该用户名已被使用。'}, status=status.HTTP_400_BAD_REQUEST)
        if role not in dict(CustomUser.ROLE_CHOICES):
            role = CustomUser.ROLE_STUDENT
        try:
            user = CustomUser.objects.create_user(
                username=username,
                password=password,
                role=role
            )
            return Response({'detail': '注册成功！', 'id': user.id, 'username': user.username, 'role': user.role},
                            status=status.HTTP_201_CREATED)
        except Exception as e:
            print(f"User registration error: {e}")
            return Response({'detail': '注册失败，请稍后再试。'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# -----------------------------------------------------------------
# 【 Stripe Webhook API 】 (保持不变)
# -----------------------------------------------------------------
class StripeWebhookView(APIView):
    def post(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        event = None
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, webhook_secret
            )
        except ValueError as e:
            return Response({'detail': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            return Response({'detail': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            course_id = session.get('metadata', {}).get('course_id')
            user_id = session.get('metadata', {}).get('user_id')
            if course_id and user_id:
                try:
                    student = CustomUser.objects.get(pk=user_id)
                    course = Course.objects.get(pk=course_id)
                    Enrollment.objects.get_or_create(
                        student=student,
                        course=course
                    )
                    print(f"WEBHOOK: 课程 {course.title} 的注册记录已创建。")
                except Exception as e:
                    return Response({'detail': f'Enrollment creation failed: {str(e)}'},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response({'success': True}, status=status.HTTP_200_OK)