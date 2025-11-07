from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from .models import (
    Course, CustomUser, Module, Lesson, Enrollment,
    Category, InstructorApplication, Comment
)
from rest_framework.generics import RetrieveUpdateAPIView, ListAPIView
from rest_framework.permissions import IsAuthenticated, BasePermission, IsAdminUser, IsAuthenticatedOrReadOnly
from .serializers import (
    CourseDetailSerializer,
    CourseListSerializer,
    UserSerializer,
    ModuleSerializer,
    LessonSerializer,
    CategorySerializer,
    InstructorApplicationSerializer,
    CommentSerializer
)
from .tasks import process_video_upload
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import filters


# -----------------------------------------------------------------
# 权限: 讲师和管理员 (不变)
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
    queryset = Course.objects.all().order_by('-created_at')
    parser_classes = [MultiPartParser, FormParser]
    filter_backends = [filters.SearchFilter]
    search_fields = ['title', 'description', 'instructor__username']

    def get_queryset(self):
        queryset = Course.objects.all().order_by('-created_at')
        category_slug = self.request.query_params.get('category')
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [IsInstructorOrAdmin()]

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        return CourseDetailSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    # 【【【已修改：移除了 Price】】】
    def create(self, request, *args, **kwargs):
        if not request.user.role in [CustomUser.ROLE_INSTRUCTOR, CustomUser.ROLE_ADMIN]:
            return Response(
                {"detail": "只有讲师或管理员才能创建课程。"},
                status=status.HTTP_403_FORBIDDEN
            )
        title = request.data.get('title')
        description = request.data.get('description')
        cover_image_file = request.data.get('cover_image')
        category_id = request.data.get('category')

        if not title or not description:
            return Response(
                {"detail": "缺少标题或描述"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            category = None
            if category_id:
                category = Category.objects.get(pk=category_id)
            course = Course.objects.create(
                title=title,
                description=description,
                instructor=request.user,
                cover_image=cover_image_file,
                category=category
                # (Price 已移除)
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
# 分类、章节、课时视图 (不变)
# -----------------------------------------------------------------
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]


class ModuleViewSet(viewsets.ModelViewSet):
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [permissions.IsAuthenticatedOrReadOnly()]
        return [IsInstructorOrAdmin()]


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
# 申请、讲师、用户视图 (不变)
# -----------------------------------------------------------------
class InstructorApplicationViewSet(viewsets.ModelViewSet):
    queryset = InstructorApplication.objects.all().order_by('-created_at')
    serializer_class = InstructorApplicationSerializer

    def get_permissions(self):
        if self.action == 'create':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_queryset(self):
        if self.request.user.role == CustomUser.ROLE_ADMIN:
            return InstructorApplication.objects.all().order_by('-created_at')
        return InstructorApplication.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        status = request.data.get('status')
        if status not in [InstructorApplication.STATUS_APPROVED, InstructorApplication.STATUS_REJECTED]:
            return Response({"detail": "无效的状态"}, status=status.HTTP_400_BAD_REQUEST)
        instance.status = status
        if status == InstructorApplication.STATUS_APPROVED:
            user_to_promote = instance.user
            user_to_promote.role = CustomUser.ROLE_INSTRUCTOR
            user_to_promote.save()
        instance.save()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class InstructorCourseListView(ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [IsInstructorOrAdmin]

    def get_queryset(self):
        user = self.request.user
        if user.role == CustomUser.ROLE_ADMIN:
            return Course.objects.all().order_by('-created_at')
        return Course.objects.filter(instructor=user).order_by('-created_at')


class UserView(RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


# -----------------------------------------------------------------
# 评论、点赞、收藏视图
# -----------------------------------------------------------------
class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all().order_by('-created_at')
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        queryset = Comment.objects.all().order_by('-created_at')
        lesson_id = self.request.query_params.get('lesson_id')
        if lesson_id:
            queryset = queryset.filter(lesson_id=lesson_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ToggleLikeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
            user = request.user
            if user in course.likes.all():
                course.likes.remove(user)
                liked = False
            else:
                course.likes.add(user)
                liked = True
            return Response(
                {'liked': liked, 'count': course.likes.count()},
                status=status.HTTP_200_OK
            )
        except Course.DoesNotExist:
            return Response({'detail': '课程不存在'}, status=status.HTTP_44_NOT_FOUND)


class ToggleFavoriteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
            user = request.user

            if user.favorited_courses.filter(pk=course.pk).exists():
                user.favorited_courses.remove(course)
                favorited = False
            else:
                user.favorited_courses.add(course)
                favorited = True

            return Response(
                {'favorited': favorited},
                status=status.HTTP_200_OK
            )
        except Course.DoesNotExist:
            return Response({'detail': '课程不存在'}, status=status.HTTP_404_NOT_FOUND)


class FavoriteCourseListView(ListAPIView):
    serializer_class = CourseListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return self.request.user.favorited_courses.all().order_by('-created_at')


# -----------------------------------------------------------------
# 用户注册 API (不变)
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