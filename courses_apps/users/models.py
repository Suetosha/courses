from django.contrib.auth.models import AbstractUser
from django.db import models

from courses_apps.courses.models import Course, Chapter
from courses_apps.tests.models import TestTask


# Модель пользователей
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


# Модель группы
class Group(models.Model):
    number = models.CharField(max_length=30, null=False)
    year = models.IntegerField(null=False)

    def __str__(self):
        return f'Группа: {self.number} ({self.year})'


# Модель подписок
class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


# Модель прогресса по главам
class ChapterProgress(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)


# Модель прогресса по выполненным заданиям. Добавляются в том случае, если задание выполнено
class TaskProgress(models.Model):
    test_task = models.ForeignKey(TestTask, on_delete=models.CASCADE)
    chapter_progress = models.ForeignKey(ChapterProgress, on_delete=models.CASCADE)



