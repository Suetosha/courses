from django.db import models
from courses_apps.users.models import User


class Category(models.Model):
    name = models.CharField(max_length=50)


class Course(models.Model):
    STATUS_CHOICES = [
        ('published', 'Published'),
        ('unpublished', 'Unpublished'),
    ]
    title = models.CharField(max_length=100)
    description = models.TextField(null=False)
    status = models.CharField(choices=STATUS_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)



class Chapter(models.Model):
    title = models.CharField(max_length=100, null=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)


class Content(models.Model):
    text = models.TextField(null=True)
    video = models.CharField(max_length=100, null=True)
    files = models.CharField(max_length=100, null=True)
    chapter = models.OneToOneField(Chapter, on_delete=models.CASCADE)


class Test(models.Model):
    question = models.TextField(null=False)
    answer_options = models.TextField(null=True)
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    correct_answer = models.TextField(null=False)
