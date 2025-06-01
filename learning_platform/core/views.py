import stripe
from django.contrib.auth import authenticate
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.conf import settings
from django.views.decorators.cache import cache_page
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.decorators import action
from .models import Course, Payment, Enrollment
from .serializers import (
    CourseSerializer,
    RegisterSerializer,
    EnrollmentSerializer,
    PaymentSerializer,
)
from .permissions import IsInstructor, IsStudent


stripe.api_key = settings.STRIPE_SECRET_KEY


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

    @action(detail=False, methods=["get"], url_path="search")
    def search(self, request):
        query = request.query_params.get("q", "")
        if not query:
            return Response(
                {"error": 'Query parameter "q" is required'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        search_query = SearchQuery(query)
        queryset = (
            Course.objects.filter(search_vector=search_query)
            .annotate(rank=SearchRank(search_vector=search_query))
            .order_by("-rank")
        )

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


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


class PaymentView(APIView):
    permission_classes = [IsStudent]

    def post(self, request):
        course_id = request.data.get("course_id")
        token = request.data.get("stripe_token")  # from frontend (e.g. Stripe.js)

        try:
            course = Course.objects.get(id=course_id, is_active=True)
            charge = stripe.Charge.create(
                amount=int(course.price * 100),  # convert to cents
                currency="usd",
                source=token,
                description=f"Payment for {course.title}",
            )
            payment = Payment.objects.create(
                user=request.user,
                course=course,
                amount=course.price,
                stripe_payment_id=charge.id,
                status="completed",
            )
            # Auto-enroll after successful payment
            Enrollment.objects.create(student=request.user, course=course)
            return Response(
                {"message": "Payment and enrollment successful"},
                status=status.HTTP_201_CREATED,
            )
        except Course.DoesNotExist:
            return Response(
                {"error": "Course not found"}, status=status.HTTP_404_NOT_FOUND
            )
        except stripe.error.StripeError as e:
            Payment.objects.create(
                user=request.user,
                course=course,
                amount=course.price,
                strip_payment_id="",
                status="failed",
            )
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
