from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from django.views.decorators.cache import cache_page
from .models import Course
from .serializers import CourseSerializer, RegisterSerializer, EnrollmentSerializer
from .permissions import IsInstructor, IsStudent


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.select_related("instructor")
    serializer_class = CourseSerializer
    permission_classes = [IsAuthenticated]

    @cache_page(60 * 15)  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    # use get_permissions for dynamic permission logic
    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsInstructor()]
        elif self.action == "enroll":
            return [IsStudent()]
        return [IsAuthenticated()]

    @action(detail=True, methods=["post"], url_path="enroll")
    def enroll(self, request, pk=None):
        course = self.get_object()
        data = {"course": course.id, "student": request.user.id}
        serializer = EnrollmentSerializer(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Enrolled successfully"}, status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RegisterView(APIView):
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {
                    "id": user.id,
                    "email": user.email,
                    "username": user.username,
                    "role": user.role,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user = authenticate(email=email, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response(
                {
                    "token": token.key,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "username": user.username,
                        "role": user.role,
                    },
                },
                status=status.HTTP_200_OK,
            )
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )
