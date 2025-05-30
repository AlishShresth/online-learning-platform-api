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
