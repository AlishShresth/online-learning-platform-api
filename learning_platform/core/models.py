from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex


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
        on_delete=models.CASCADE,
        limit_choices_to={"role": "instructor"},
        related_name="courses",
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)  # Added for partial indexing
    search_vector = SearchVectorField(null=True)  # for full-text search

    class Meta:
        indexes = [
            models.Index(
                fields=["instructor", "created_at"]
            ),  # Composite index for instructor-specific queries
            models.Index(
                fields=["title"],
                condition=models.Q(is_active=True),
                name="active_courses_idx",
            ),  # Partial index on title where is_active=True optimizes queries like Course.objects.filter(is_active=True, title__icontains='Python').
            # condition=Q(is_active=True) creates a index with WHERE is_active=true.
            GinIndex(fields=["search_vector"], name="course_search_idx"),
        ]

    def __str__(self):
        return self.title


class Enrollment(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={"role": "student"},
        related_name="enrollments",
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="enrollments"
    )
    enrollment_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=(
            ("active", "Active"),
            ("completed", "Completed"),
            ("dropped", "Dropped"),
        ),
        default="active",
    )

    class Meta:
        indexes = [
            models.Index(fields=["student", "course"])  # for fast enrollment lookups
        ]
        unique_together = [["student", "course"]]  # prevent duplicate enrollments

    def __str__(self):
        return f"{self.student.email} enrolled in {self.course.title}"


class Payment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="payments")
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="payments"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_payment_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(
        max_length=20,
        choices=(
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ),
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "created_at"]),  # for user payment history
            models.Index(fields=["stripe_payment_id"]),  # for fast stripe lookups
        ]

    def __str__(self):
        return f"{self.user.email} paid {self.amount} for {self.course.title}"


class Review(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="reviews")
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE(),
        related_name="reviews",
        limit_choices_to={"role": "student"},
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["course", "created_at"]),  # For course review lists
        ]
        unique_together = [["student", "course"]]  # one review per student per course

    def __str__(self):
        return (
            f"{self.student.email} reviewed {self.course.title} ({self.rating} stars)"
        )
