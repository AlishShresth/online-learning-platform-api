from rest_framework import serializers
from .models import User, Course, Enrollment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "email", "username", "role", "bio"]


class CourseSerializer(serializers.ModelSerializer):
    instructor = UserSerializer(read_only=True)

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "instructor",
            "price",
            "created_at",
            "updated_at",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ["email", "username", "password", "role", "bio"]

    def validate_role(self, value):
        # Restrict 'admin' role during registration
        if value == "admin":
            raise serializers.ValidationError("Cannot register as admin.")
        return value

    def create(self, validated_data):
        user = User.objects.create(
            email=validated_data["email"],
            username=validated_data["username"],
            role=validated_data["role"],
            bio=validated_data("bio", ""),
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class EnrollmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Enrollment
        fields = ["id", "student", "course", "enrollment_date", "status"]
        read_only_fields = ["enrollment_date", "student"]

    def validate(self, data):
        # Ensure the course exists and is active
        course = data["course"]
        if not course.is_active:
            raise serializers.ValidationError("Cannot enroll in an inactive course.")
        # Check if already enrolled
        if Enrollment.objects.filter(
            student=self.context["request"].user, course=course
        ).exists():
            raise serializers.ValidationError("Already enrolled in this course.")
        return data
