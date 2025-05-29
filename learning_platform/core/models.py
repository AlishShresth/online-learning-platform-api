from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("instructor", "Instructor"),
        ("admin", "Admin"),
    )
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    bio = models.TextField(blank=True, null=True)

    USERNAME_FIELD = "email"  # Use email for authentication
    REQUIRED_FIELDS = ["username", "role"]  # Fields prompted when creating a superuser

    def __str__(self):
        return self.email
