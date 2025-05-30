from rest_framework import serializers
from .models import User, Course


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
