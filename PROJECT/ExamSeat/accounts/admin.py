from django.contrib import admin

from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'name', 'department', 'student_class', 'academic_year')
    search_fields = ('roll_number', 'name', 'department')
    list_filter = ('academic_year', 'student_class', 'department')


from .models import Room

@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_no', 'benches', 'rows', 'columns', 'capacity')
    search_fields = ('room_no',)
    list_filter = ('rows', 'columns')
    ordering = ('room_no',)



