from django.db import models


# Модель тестов. Один тест может содержать несколько заданий
class Test(models.Model):
    chapter = models.OneToOneField("courses.Chapter", on_delete=models.CASCADE)
    tasks = models.ManyToManyField(
        "Task",
        blank=True,
        through='TestTask',
        related_name="tests"
    )


# Модель заданий
class Task(models.Model):
    question = models.TextField(null=False)
    is_text_input = models.BooleanField(default=False)
    is_multiple_choice = models.BooleanField(default=False)
    is_compiler = models.BooleanField(default=False)


    def __str__(self):
        return self.question


# Связующая модель между тестом и заданиями
class TestTask(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)


# Модель ответов
class Answer(models.Model):
    text = models.TextField(null=False)
    is_correct = models.BooleanField(default=False)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)