from django.db import models


class Specializations(models.TextChoices):
    PYTHON = "Python"
    JAVA = "Java"
    DATA = "Data"
    Frontend = "Frontend"


class Mentor(models.Model):
    name = models.CharField(max_length=70)
    specialization = models.CharField(max_length=30, choices=Specializations.choices)

    def __str__(self):
        return f"{self.name}"


class Student(models.Model):
    name = models.CharField(max_length=70)
    bio = models.TextField()
    mentor = models.ForeignKey(to=Mentor, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.name}"
