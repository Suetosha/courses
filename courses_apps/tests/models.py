from django.db import models
from typing import Type


# Модель тестов. Один тест может содержать несколько заданий
class Test(models.Model):
    chapter = models.OneToOneField("courses.Chapter", on_delete=models.CASCADE)
    tasks = models.ManyToManyField(
        "Task",
        blank=True,
        through='TestTask',
        related_name="tests"
    )

    objects: Type[models.Manager] = models.Manager()


# Модель заданий
class Task(models.Model):
    question = models.TextField(null=False)
    is_text_input = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=False)
    is_compiler = models.BooleanField(default=False)
    POINT_CHOICES = [(i, str(i)) for i in range(1, 6)]
    point = models.IntegerField(choices=POINT_CHOICES, default=1)

    objects: Type[models.Manager] = models.Manager()

    def __str__(self):
        return self.question


# Связующая модель между тестом и заданиями
class TestTask(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    objects: Type[models.Manager] = models.Manager()


# Модель ответов
class Answer(models.Model):
    text = models.TextField(null=False)
    is_correct = models.BooleanField(default=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    objects: Type[models.Manager] = models.Manager()


# Модель контрольных тестов
class ControlTest(models.Model):
    title = models.CharField(max_length=100, null=False)

    objects: Type[models.Manager] = models.Manager()

    def __str__(self):
        return self.title


# Связующая модель между тестов и заданиями
class ControlTestTask(models.Model):
    control_test = models.ForeignKey(ControlTest, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)

    objects: Type[models.Manager] = models.Manager()
