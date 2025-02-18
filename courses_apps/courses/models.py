from django.db import models
from courses_apps.users.models import User




class Category(models.Model):
    name = models.CharField(max_length=50, null=False)

    def __str__(self):
        return self.name


class Course(models.Model):
    STATUS_CHOICES = [
        ('published', 'Опубликовано'),
        ('unpublished', 'Не опубликовано'),
    ]
    title = models.CharField(max_length=100, null=False)
    description = models.TextField(null=False)
    status = models.CharField(choices=STATUS_CHOICES)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)



class Chapter(models.Model):
    title = models.CharField(max_length=100, null=False)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Content(models.Model):
    text = models.TextField(null=True)
    video = models.FileField(upload_to='video/', null=True, blank=True)
    files = models.FileField(upload_to='pdf_files/', null=True, blank=True)
    chapter = models.OneToOneField(Chapter, on_delete=models.CASCADE)


class Test(models.Model):
    chapter = models.OneToOneField(Chapter, on_delete=models.CASCADE)
    tasks = models.ManyToManyField(
        "Task",
        blank=True,
        through='TestTask',
        related_name="tests"
    )


class Task(models.Model):
    question = models.TextField(null=False)
    is_text_input = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=False)
    is_compiler = models.BooleanField(default=False)


    def __str__(self):
        return self.question


class TestTask(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)


class ChapterProgress(models.Model):
    chapter = models.ForeignKey(Chapter, on_delete=models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)


class TaskProgress(models.Model):
    test_task = models.ForeignKey(TestTask, on_delete=models.CASCADE)
    chapter_progress = models.ForeignKey(ChapterProgress, on_delete=models.CASCADE)


class Answer(models.Model):
    text = models.TextField(null=False)
    is_correct = models.BooleanField(default=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)