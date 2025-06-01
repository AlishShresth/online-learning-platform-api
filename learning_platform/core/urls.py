from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CourseViewSet, RegisterView, LoginView, PaymentView


router = DefaultRouter()
router.register(r"courses", CourseViewSet, basename="courses")


urlpatterns = [
    path("api/", include(router.urls)),
    path("api/register/", RegisterView.as_view(), name="register"),
    path("api/login/", LoginView.as_view(), name="login"),
    path("api/pay/", PaymentView.as_view(), name="pay"),
]
