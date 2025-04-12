from typing import Type

from django.db import models
from courses_apps.tests.models import TestTask


# Модель категории
class Category(models.Model):
    name = models.CharField(max_length=50, null=False)

    objects: Type[models.Manager] = models.Manager()

    def __str__(self):
        return self.name


# Модель курса
class Course(models.Model):
    STATUS_CHOICES = [
        ('published', 'Опубликовано'),
        ('unpublished', 'Не опубликовано'),
    ]
    title = models.CharField(max_length=100, null=False)
    description = models.TextField(null=False)
    status = models.CharField(choices=STATUS_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    objects: Type[models.Manager] = models.Manager()

    def __str__(self):
        return self.title


# Модель главы
class Chapter(models.Model):
    title = models.CharField(max_length=100, null=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    objects: Type[models.Manager] = models.Manager()

    def __str__(self):
        return self.title


# Модель контента для главы
class Content(models.Model):
    text = models.TextField(null=True)
    video = models.FileField(upload_to='video/', null=True, blank=True)
    files = models.FileField(upload_to='pdf_files/', null=True, blank=True)
    chapter = models.OneToOneField(Chapter, on_delete=models.CASCADE)

    objects: Type[models.Manager] = models.Manager()
