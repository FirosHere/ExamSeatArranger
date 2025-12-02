from django.db import models

class Student(models.Model):
    roll_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100)
    student_class = models.CharField(max_length=50, blank=True, null=True)
    academic_year = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"{self.roll_number} - {self.name}"


class Room(models.Model):
    room_no = models.CharField(max_length=10, unique=True)
    benches = models.IntegerField()
    rows = models.IntegerField()
    columns = models.IntegerField()
    capacity = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'rooms'
        ordering = ['room_no']

    def save(self, *args, **kwargs):
        self.capacity = self.benches * 2
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Room {self.room_no} ({self.benches} benches, {self.capacity} capacity)"
