from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import Course


@receiver(post_save, sender=Course)
def invalidate_course_cache(sender, instance, **kwargs):
    cache.delete("course_list_cache")
