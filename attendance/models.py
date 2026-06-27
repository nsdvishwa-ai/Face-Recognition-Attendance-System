from django.db import models

class Employee(models.Model):
    employee_id = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='employees/')
    face_encoding = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    
class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    time = models.TimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.employee.name} - {self.date}"
    
class MonthlyWorkingDays(models.Model):
    month = models.IntegerField()
    year = models.IntegerField()
    working_days = models.IntegerField()

    def __str__(self):
        return f"{self.month}/{self.year} - {self.working_days} days"