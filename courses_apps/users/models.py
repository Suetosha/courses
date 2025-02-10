from django.contrib.auth.models import AbstractUser
from django.db import models
from django.contrib.postgres.fields import ArrayField


class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]
    username = models.CharField(max_length=30, unique=True)
    password = models.CharField(max_length=255, null=False)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    completed_chapters = ArrayField(models.IntegerField(), default=list)
    completed_tests = ArrayField(models.IntegerField(), default=list)
    group_number = models.CharField(max_length=50)


