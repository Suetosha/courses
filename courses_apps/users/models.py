from django.contrib.auth.models import AbstractUser
from django.db import models


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
    groups = models.ManyToManyField(
        "Group",
        blank=True
    )



class Group(models.Model):
    number = models.CharField(max_length=30, null=False)
    year = models.IntegerField(null=False)







