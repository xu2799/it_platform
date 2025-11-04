from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import (
    Course, CustomUser, Module, Lesson, Enrollment,
    Category, InstructorApplication  # <-- 【【【新增】】】
)
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser
from .serializers import (
    CourseDetailSerializer,
    CourseListSerializer,
    UserSerializer,
    ModuleSerializer,
    LessonSerializer,
    CategorySerializer,  # <-- 【【【新增】】】
    InstructorApplicationSerializer  # <-- 【【【新增】】】
)
from .tasks import process_video_upload
import stripe
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import filters  # <-- 【【【新增：搜索功能】】】


# -----------------------------------------------------------------
# 权限: 讲师和管理员
# -----------------------------------------------------------------
class IsInstructorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]


# -----------------------------------------------------------------
# 课程“视图集合” - 【【已修改】】
# -----------------------------------------------------------------
class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all().order_by('-created_at')  # 默认按创建时间排序
    serializer_class = CourseDetailSerializer
    parser_classes = [MultiPartParser, FormParser]

    # 【【【新增：搜索和过滤】】】
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'instructor__username']  # 可以搜索标题、描述、讲师名

    # 【【【新增：按分类过滤】】】
    def get_queryset(self):
        queryset = Course.objects.all().order_by('-created_at')

        # 1. 按分类过滤 (例如 /api/courses/?category=python)
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        # 2. (搜索功能由 filter_backends 自动处理)

        return queryset

    # (动态权限 - 不变)
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [IsInstructorOrAdmin()]

    # (动态序列化器 - 不变)
    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    # (安全检索 - 不变)
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        user = request.user
        is_enrolled = False
        is_owner_or_admin = False

        if user.is_authenticated:
            is_enrolled = Enrollment.objects.filter(student=user, course=instance).exists()
            is_owner_or_admin = (instance.instructor == user) or (user.role == CustomUser.ROLE_ADMIN)

        if is_enrolled or is_owner_or_admin:
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        else:
            serializer = CourseListSerializer(instance)
            data = serializer.data
            # data.pop('modules', None) # CourseListSerializer 已经不包含 modules
            return Response(data)

    # 【【【修改：create 方法以接受 category】】】
    def create(self, request, *args, **kwargs):
        if not request.user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]:
            return Response(
                {"detail": "只有讲师或管理员才能创建课程。"},
                status=status.HTTP_403_FORBIDDEN
            )

        # 从 request.data 中获取所有数据
        title = request.data.get('title')
        description = request.data.get('description')
        price = request.data.get('price')
        cover_image_file = request.data.get('cover_image')
        category_id = request.data.get('category')  # <-- 【【【新增】】】

        if not title or not description or not price:
            return Response(
                {"detail": "缺少标题、描述或价格"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            category = None
            if category_id:
                category = Category.objects.get(pk=category_id)  # <-- 【【【新增】】】

            course = Course.objects.create(
                title=title,
                description=description,
                price=price,
                instructor=request.user,
                cover_image=cover_image_file,
                category=category  # <-- 【【【新增】】】
            )

            serializer = self.get_serializer(course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Category.DoesNotExist:
            return Response(
                {"detail": "所选分类不存在。"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"detail": f"创建课程失败: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )


# -----------------------------------------------------------------
# 【【【新增】】】: 课程分类“视图集合”
# -----------------------------------------------------------------
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    一个只读 API 端点, 用于列出所有课程分类。
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]  # 任何人都可以看


# -----------------------------------------------------------------
# 章节“视图集合” (不变)
# -----------------------------------------------------------------
class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [IsInstructorOrAdmin()]


# -----------------------------------------------------------------
# 课时“视图集合” (不变)
# -----------------------------------------------------------------
class LessonViewSet(viewsets.ModelViewSet):
    queryset = Lesson.objects.all()
    serializer_class = LessonSerializer
    parser_classes = [MultiPartParser, FormParser]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsInstructorOrAdmin()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
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
            if module.course.instructor != request.user and request.user.role != CustomUser.ROLE_ADMIN:
                return Response(
                    {"detail": "你没有权限向这个课程添加课时。"},
                    status=status.HTTP_403_FORBIDDEN
                )
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
# 【【【新增】】】: 讲师申请“视图集合”
# -----------------------------------------------------------------
class InstructorApplicationViewSet(viewsets.ModelViewSet):
    queryset = InstructorApplication.objects.all().order_by('-created_at')
    serializer_class = InstructorApplicationSerializer

    def get_permissions(self):
        # 学生只能 'create' (提交申请)
        if self.action == 'create':
            return [IsAuthenticated()]
        # 只有管理员能 'list', 'retrieve', 'update', 'destroy' (审批)
        return [IsAdminUser()]

    def get_queryset(self):
        # 管理员获取所有申请
        if self.request.user.role == CustomUser.ROLE_ADMIN:
            return InstructorApplication.objects.all().order_by('-created_at')
        # 学生只能看到自己的申请
        return InstructorApplication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # 自动将申请人设为当前登录用户
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        # 这是“审批”的核心逻辑
        instance = self.get_object()
        status = request.data.get('status')

        if status not in [InstructorApplication.STATUS_APPROVED, InstructorApplication.STATUS_REJECTED]:
            return Response({"detail": "无效的状态"}, status=status.HTTP_400_BAD_REQUEST)

        # 更新申请状态
        instance.status = status

        # 【【【核心】】】: 如果批准, 升级用户角色
        if status == InstructorApplication.STATUS_APPROVED:
            user_to_promote = instance.user
            user_to_promote.role = CustomUser.ROLE_INSTRUCTOR
            user_to_promote.save()

        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


# -----------------------------------------------------------------
# 用户“我”视图 (不变)
# -----------------------------------------------------------------
class UserView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# -----------------------------------------------------------------
# Stripe 支付 API (不变)
# -----------------------------------------------------------------
class CreateCheckoutSessionView(APIView):
    # ... (代码不变) ...
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
# 用户注册 API (不变)
# -----------------------------------------------------------------
class RegisterView(APIView):
    # ... (代码不变) ...
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
# Stripe Webhook API (不变)
# -----------------------------------------------------------------
class StripeWebhookView(APIView):
    # ... (代码不变) ...
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