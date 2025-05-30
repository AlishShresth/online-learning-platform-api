from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ("student", "Student"),
        ("instructor", "Instructor"),
        ("admin", "Admin"),
    )
    email = models.EmailField(unique=True, db_index=True)  # Index for fast login
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    bio = models.TextField(blank=True, null=True)

    USERNAME_FIELD = "email"  # Use email for authentication
    REQUIRED_FIELDS = ["username", "role"]  # Fields prompted when creating a superuser

    class Meta:
        indexes = [
            models.Index(fields=["role"]),  # Index for filtering by role
        ]

    def __str__(self):
        return self.email


class Course(models.Model):
    title = models.CharField(max_length=250, db_index=True)
    description = models.TextField()
    instructor = models.ForeignKey(
        User,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={"role": "instructor"},
        related_name="courses",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["instructor", "created_at"]
            ),  # Composite index for instructor-specific queries
        ]

    def __str__(self):
        return self.title
