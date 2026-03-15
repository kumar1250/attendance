from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='admin')

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    teacher = models.ForeignKey('Teacher', on_delete=models.SET_NULL, null=True, related_name='subjects')
    class_name = models.CharField(max_length=50, blank=True)
    section = models.CharField(max_length=10, blank=True)
    branch = models.CharField(max_length=50, blank=True)
    semester = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.name} ({self.code}) - {self.branch} {self.section} Sem {self.semester}"

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'teacher'})
    phone = models.CharField(max_length=15)

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, limit_choices_to={'role': 'student'})
    roll_number = models.CharField(max_length=20, unique=True)
    phone = models.CharField(max_length=15)
    class_name = models.CharField(max_length=50) # e.g. "B.Tech"
    branch = models.CharField(max_length=50, blank=True)
    section = models.CharField(max_length=10)
    semester = models.IntegerField(default=1)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.roll_number}) - {self.branch} {self.section} Sem {self.semester}"

class Timetable(models.Model):
    DAYS = (
        ('Monday', 'Monday'),
        ('Tuesday', 'Tuesday'),
        ('Wednesday', 'Wednesday'),
        ('Thursday', 'Thursday'),
        ('Friday', 'Friday'),
        ('Saturday', 'Saturday'),
    )
    day = models.CharField(max_length=15, choices=DAYS)
    hour = models.IntegerField() # Period number
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    class_name = models.CharField(max_length=50)
    branch = models.CharField(max_length=50, blank=True)
    section = models.CharField(max_length=10)
    semester = models.IntegerField(default=1)

    class Meta:
        unique_together = ('day', 'hour', 'branch', 'section', 'semester')

class Attendance(models.Model):
    STATUS_CHOICES = (
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    date = models.DateField()
    hour = models.IntegerField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'subject', 'date', 'hour')
