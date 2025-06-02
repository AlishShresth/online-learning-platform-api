from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_payment_confirmation_email(user_email, course_title):
    send_mail(
        subject="Payment Confirmation",
        message=f"Thank you for enrolling in {course_title}!",
        from_email="no-reply@learningplatform.com",
        recipient_list=[user_email],
        fail_silently=False,
    )
