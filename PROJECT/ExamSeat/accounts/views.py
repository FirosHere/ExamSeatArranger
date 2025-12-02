from itertools import count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.conf import settings
from types import SimpleNamespace
from .models import Room
import random

import csv
import os
from collections import deque
from .forms import UploadCSVForm, StudentForm

from .models import Student, Room



# ----------------- AUTH -----------------
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        messages.error(request, 'Invalid username or password')
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def home_view(request):
    return render(request, 'home.html')


# ----------------- STUDENTS -----------------
# accounts/views.py

import csv
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import UploadCSVForm
from .models import Student

def upload_students(request):
    if request.method == 'POST' and 'upload_csv' in request.POST:
        form = UploadCSVForm(request.POST, request.FILES)
        if form.is_valid():
            csv_file = request.FILES['file']
            decoded_file = csv_file.read().decode('utf-8').splitlines()

            # Detect delimiter
            sample_line = decoded_file[0]
            delimiter = '\t' if '\t' in sample_line else ','

            reader = csv.DictReader(decoded_file, delimiter=delimiter)

            # Normalize headers
            raw_headers = [h.strip().lower().replace(" ", "_") for h in reader.fieldnames]

            # Required fields (allow flexible naming)
            required_fields = ['roll_number', 'name','department', 'student_class', 'academic_year']
               # Check required fields
            if 'roll_number' not in raw_headers:
                messages.error(request, "❌ The CSV file must contain a 'roll_number' column.")
                return redirect('upload_students')

            if not any(h in raw_headers for h in ['name', 'student_name']):
                messages.error(request, "❌ The CSV file must contain a 'name' or 'student_name' column.")
                return redirect('upload_students')

        

            # Helper to safely extract values from row
            def get_value(row, *fields):
                normalized_row = {k.strip().lower().replace(" ", "_"): v for k, v in row.items()}
                for field in fields:
                    if field in normalized_row and normalized_row[field]:
                        return normalized_row[field].strip()
                return ""

            created_count = 0
            for row in reader:
                roll = get_value(row, 'roll_number')
                name = get_value(row, 'name', 'student_name')   # ✅ flexible matching

                if roll and name:
                    Student.objects.update_or_create(
                        roll_number=roll,
                        defaults={
                            'name': name,
                            'department': get_value(row, 'department'),
                            'student_class': get_value(row, 'student_class'),
                            'academic_year': get_value(row, 'academic_year'),
                        }
                    )
                    created_count += 1

            if created_count > 0:
                messages.success(request, f"✅ Successfully uploaded {created_count} students.")
            else:
                messages.warning(request, "⚠️ No valid student records were uploaded.")

            return redirect('upload_students')
    else:
        form = UploadCSVForm()

    return render(request, 'upload_students.html', {'form': form})




# Manual Add Student
def add_student_manual(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student added successfully!")
            return redirect('upload_students')
        else:
            messages.error(request, "Failed to add student. Please check the form.")
    else:
        form = StudentForm()
    return render(request, 'upload_students.html', {'form': form})


# Reset Students DB
def reset_students_db(request):
    if request.method == 'POST':
        Student.objects.all().delete()
        messages.success(request, "All student records deleted successfully!")
        return redirect('upload_students')
# ----------------- ROOMS -----------------
def add_room(request):
    if request.method == "POST":
        room_no = request.POST.get('room_no')
        try:
            benches = int(request.POST.get('benches'))
            rows = int(request.POST.get('rows'))
            columns = int(request.POST.get('columns'))
        except ValueError:
            messages.error(request, "Invalid numbers.")
            return redirect('add_room')

        if Room.objects.filter(room_no=room_no).exists():
            messages.error(request, "Room number exists.")
            return redirect('add_room')

        Room.objects.create(room_no=room_no, benches=benches, rows=rows, columns=columns)
        messages.success(request, "Room added successfully.")
        return redirect('add_room')

    rooms = Room.objects.all()
    return render(request, 'add_room.html', {'rooms': rooms})


def delete_room(request, room_id):
    room = get_object_or_404(Room, id=room_id)
    room.delete()
    messages.success(request, f"Room {room.room_no} deleted.")
    return redirect('add_room')


# ----------------- SEAT ALLOCATION -----------------
def generate_seats(students):
    """
    Allocate students to benches in rooms, ensuring no duplicates.
    Returns a list of dictionaries per room.
    """
    # Shuffle students for fairness
    students = list(students)
    random.shuffle(students)

    # Group by department
    dept_groups = {}
    for student in students:
        dept_groups.setdefault(student.department, []).append(student)

    dept_queues = {dept: deque(studs) for dept, studs in dept_groups.items()}
    dept_cycle = deque(dept_queues.keys())

    allocation = []

    for room in Room.objects.all():
        benches_list = []
        bench_no = 1
        room_full = False

        for r in range(room.rows):
            row_data = []
            for c in range(room.columns):
                if bench_no <= room.benches:
                    seat1 = None
                    seat2 = None

                    # Allocate first seat
                    while dept_cycle and not seat1:
                        dept = dept_cycle[0]
                        if dept_queues[dept]:
                            seat1 = dept_queues[dept].popleft()
                        else:
                            dept_cycle.popleft()
                            continue
                        dept_cycle.rotate(-1)

                    # Allocate second seat
                    while dept_cycle and not seat2:
                        dept = dept_cycle[0]
                        if dept_queues[dept]:
                            seat2 = dept_queues[dept].popleft()
                        else:
                            dept_cycle.popleft()
                            continue
                        dept_cycle.rotate(-1)

                    if not seat1 and not seat2:
                        room_full = True
                        break

                    row_data.append({
                        "bench_no": bench_no,
                        "seat1": SimpleNamespace(**seat1.__dict__) if seat1 else None,
                        "seat2": SimpleNamespace(**seat2.__dict__) if seat2 else None,
                    })
                    bench_no += 1
                else:
                    row_data.append({"bench_no": None})
            benches_list.append(row_data)
            if room_full:
                break

        allocation.append({
            "classroom": room.room_no,
            "grid": benches_list,
        })

        if all(not q for q in dept_queues.values()):
            break

    return allocation

# ----------------- Views -----------------

def view_allotments(request):
    """Show list of all rooms"""
    rooms = Room.objects.all()
    return render(request, 'view_allotments.html', {'rooms': rooms})

def view_room_allocation(request, room_no):
    """Show allocation for a specific room"""
    room = get_object_or_404(Room, room_no=room_no)
    students = Student.objects.all()
    allocation = generate_seats(students)
    # Find the room allocation in list
    room_alloc = next((r for r in allocation if r['classroom'] == room.room_no), None)
    return render(request, 'room_allocation.html', {'room': room, 'allocation': room_alloc})

def generate_seats_view(request):
    """Show all room allocations together"""
    students = Student.objects.all()
    allocation = generate_seats(students)
    return render(request, 'generate_seats.html', {'allocations': allocation})


def view_allotments(request):
    """Show list of all rooms with links to allocations"""
    rooms = Room.objects.all()
    return render(request, 'view_allotments.html', {'rooms': rooms})


def view_room_allocation(request, room_no):
    """Show allocation for a specific room"""
    room = get_object_or_404(Room, room_no=room_no)
    students = Student.objects.all()
    allocation = generate_seats(students)
    
    # Find allocation for this room
    room_alloc = next((r for r in allocation if r['classroom'] == room.room_no), None)
    return render(request, 'room_seats.html', {'room': room, 'allocation': room_alloc})






from django.shortcuts import render
from .models import Student
from collections import defaultdict

def generate_seats(request):
    try:
        # Get all students ordered by department and academic year
        students = Student.objects.all().order_by('department', 'academic_year', 'roll_number')

        # Group students by department and academic year
        grouped_students = defaultdict(lambda: defaultdict(list))
        for student in students:
            grouped_students[student.department][student.academic_year].append(student)

        context = {
            'grouped_students': dict(grouped_students)
        }

        return render(request, 'generate_seats.html', context)

    except Exception as e:
        context = {
            'grouped_students': {},
            'error': str(e),
        }
        return render(request, 'generate_seats.html', context)




from django.shortcuts import render, redirect
from django.db.models import Count
from django.views.decorators.http import require_POST
from collections import defaultdict
from .models import Student

def generate_seats(request):
    try:
        # Handle student deletion (from delete button)
        if request.method == "POST":
            student_id = request.POST.get("student_id")
            if student_id:
                Student.objects.filter(id=student_id).delete()

        # Fetch all students ordered by academic year and department
        students = Student.objects.all().order_by('academic_year', 'department', 'roll_number')

        # Group students by academic year → department
        grouped_students = defaultdict(lambda: defaultdict(list))
        for student in students:
            grouped_students[student.academic_year][student.department].append(student)

        context = {
            'grouped_students': dict(grouped_students)
        }

        return render(request, 'generate_seats.html', context)

    except Exception as e:
        context = {
            'grouped_students': {},
            'error': str(e),
        }
        return render(request, 'generate_seats.html', context)



from django.shortcuts import render
from .models import Student

def generate_seats(request):
    try:
        success_message = None

        # --- Handle deletion by department + academic year ---
        if request.method == "POST":
            department_to_delete = request.POST.get("department_to_delete", "").strip()
            year_to_delete = request.POST.get("year_to_delete", "").strip()

            if department_to_delete and year_to_delete:
                deleted_count, _ = Student.objects.filter(
                    department__iexact=department_to_delete,
                    academic_year__iexact=year_to_delete
                ).delete()
                success_message = f"Successfully deleted {deleted_count} student(s) from {department_to_delete} - {year_to_delete}."

        # --- Get selected filters ---
        selected_year = request.GET.get('academic_year', '').strip()
        selected_department = request.GET.get('department', '').strip()

        students = Student.objects.all()
        if selected_year:
            students = students.filter(academic_year__iexact=selected_year)
        if selected_department:
            students = students.filter(department__iexact=selected_department)

        # --- Get distinct filter options ---
        academic_years = Student.objects.order_by('academic_year').values_list('academic_year', flat=True).distinct()
        departments = Student.objects.order_by('department').values_list('department', flat=True).distinct()

        context = {
            'students': students,
            'academic_years': academic_years,
            'departments': departments,
            'selected_year': selected_year,
            'selected_department': selected_department,
            'success_message': success_message,
        }
        return render(request, 'generate_seats.html', context)

    except Exception as e:
        return render(request, 'generate_seats.html', {
            'students': [],
            'academic_years': [],
            'departments': [],
            'error': str(e)
        })











from django.shortcuts import render
from django.contrib import messages
from .models import Student, Room
import random

def view_allotments(request):
    try:
        # --- Get unique filter values ---
        departments = list(Student.objects.values_list('department', flat=True).distinct())
        classes = list(Student.objects.values_list('student_class', flat=True).distinct())
        years = list(Student.objects.values_list('academic_year', flat=True).distinct())

        # --- Read filters from request ---
        selected_departments = request.GET.getlist('departments')
        selected_classes = request.GET.getlist('student_classes')
        selected_year = request.GET.get('academic_year', '')

        # --- Filter students ---
        students = Student.objects.all()
        if selected_departments:
            students = students.filter(department__in=selected_departments)
        if selected_classes:
            students = students.filter(student_class__in=selected_classes)
        if selected_year:
            students = students.filter(academic_year=selected_year)

        students = list(students)
        total_students = len(students)

        # --- Get rooms ---
        rooms = list(Room.objects.all())
        total_capacity = sum(room.capacity for room in rooms)
        rooms_with_allocations = None

        # --- Generate seat allotments ---
        if request.GET.get('generate'):
            if total_students == 0:
                messages.error(request, "No students found for the selected filters.")
            elif total_students > total_capacity:
                messages.error(
                    request,
                    f"Total students ({total_students}) exceed total room capacity ({total_capacity})."
                )
            else:
                random.shuffle(students)
                dept_groups = {}
                for s in students:
                    dept_groups.setdefault(s.department, []).append(s)

                allocation_result = []
                room_index = 0
                bench_number = 1

                while any(dept_groups.values()) and room_index < len(rooms):
                    available_depts = [d for d, lst in dept_groups.items() if lst]
                    if len(available_depts) >= 2:
                        d1, d2 = random.sample(available_depts, 2)
                        s1 = dept_groups[d1].pop(0)
                        s2 = dept_groups[d2].pop(0)
                    else:
                        d1 = available_depts[0]
                        s1 = dept_groups[d1].pop(0)
                        s2 = None

                    current_room = rooms[room_index]
                    allocation_result.append({
                        'room': current_room.room_no,
                        'bench': bench_number,
                        'left': s1,
                        'right': s2
                    })

                    bench_number += 1
                    if bench_number > current_room.benches:
                        bench_number = 1
                        room_index += 1

                # --- Group by room for table display ---
                rooms_with_allocations = {}
                for a in allocation_result:
                    rooms_with_allocations.setdefault(a['room'], []).append(a)

        context = {
            'departments': departments,
            'classes': classes,
            'years': years,
            'selected_departments': selected_departments,
            'selected_classes': selected_classes,
            'selected_year': selected_year,
            'rooms_with_allocations': rooms_with_allocations,
            'total_students': total_students,
            'total_capacity': total_capacity,
        }
        return render(request, 'view_allotments.html', context)

    except Exception as e:
        return render(request, 'view_allotments.html', {
            'departments': [],
            'classes': [],
            'years': [],
            'error': str(e)
        })















from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from .models import Room, Student

def export_pdf(request):
    departments = request.GET.get('departments', '').split(',')
    year = request.GET.get('academic_year', '')

    # Filter students
    students = Student.objects.filter(department__in=departments)
    if year:
        students = students.filter(academic_year=year)

    # Prepare PDF
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="seat_allotment.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    p.setFont("Helvetica-Bold", 16)
    p.drawString(200, y, "Seat Allocation Report")
    y -= 30

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Departments: {', '.join(departments)}")
    y -= 20
    p.drawString(50, y, f"Academic Year: {year if year else 'All'}")
    y -= 30

    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Roll No")
    p.drawString(150, y, "Name")
    p.drawString(350, y, "Department")
    y -= 15
    p.line(50, y, 550, y)
    y -= 20

    p.setFont("Helvetica", 11)
    for s in students:
        if y < 80:
            p.showPage()
            y = height - 50
        p.drawString(50, y, s.roll_number)
        p.drawString(150, y, s.name)
        p.drawString(350, y, s.department)
        y -= 20

    p.showPage()
    p.save()
    return response








from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.units import inch
from .models import Room, Student

import random

def export_pdf(request):
    departments = request.GET.get('departments', '').split(',')
    year = request.GET.get('academic_year', '')

    students = Student.objects.filter(department__in=departments)
    if year:
        students = students.filter(academic_year=year)

    students = list(students)
    random.shuffle(students)

    rooms = Room.objects.all()
    total_capacity = sum(r.capacity for r in rooms)
    total_students = len(students)

    # Create response
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="seat_allotment.pdf"'

    p = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 60

    # Title
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(width / 2, y, "Seat Allocation Report")
    y -= 40

    p.setFont("Helvetica", 12)
    p.drawString(50, y, f"Departments: {', '.join(departments)}")
    y -= 20
    p.drawString(50, y, f"Academic Year: {year if year else 'All'}")
    y -= 20
    p.drawString(50, y, f"Total Students: {total_students}")
    y -= 20
    p.drawString(50, y, f"Total Capacity: {total_capacity}")
    y -= 30

    # Validation
    if total_students > total_capacity:
        p.setFillColor(colors.red)
        p.drawString(50, y, "❌ Error: Not enough seats for all students.")
        p.save()
        return response

    # Allocation logic: 2 students per bench, different departments if possible
    benches_data = []
    for room in rooms:
        room_allocations = []
        for bench_num in range(1, room.benches + 1):
            if not students:
                break
            left = students.pop(0)
            right = None
            # Try to find a different department student
            for s in students:
                if s.department != left.department:
                    right = s
                    students.remove(s)
                    break
            room_allocations.append({"bench": bench_num, "left": left, "right": right})
        benches_data.append((room, room_allocations))

    # Draw each room table
    for room, benches in benches_data:
        if y < 150:
            p.showPage()
            y = height - 60
        p.setFillColor(colors.black)
        p.setFont("Helvetica-Bold", 13)
        p.drawString(50, y, f"Room: {room.room_no} (Capacity: {room.capacity})")
        y -= 20
        p.line(50, y, width - 50, y)
        y -= 20

        # Table headers
        p.setFont("Helvetica-Bold", 11)
        p.drawString(60, y, "Bench")
        p.drawString(120, y, "Left Seat")
        p.drawString(320, y, "Right Seat")
        y -= 15
        p.line(50, y, width - 50, y)
        y -= 10

        p.setFont("Helvetica", 10)
        for a in benches:
            if y < 100:
                p.showPage()
                y = height - 60
            p.drawString(60, y, str(a["bench"]))
            left_text = f"{a['left'].roll_number} - {a['left'].name} ({a['left'].department})"
            p.drawString(120, y, left_text)
            if a["right"]:
                right_text = f"{a['right'].roll_number} - {a['right'].name} ({a['right'].department})"
            else:
                right_text = "Empty"
            p.drawString(320, y, right_text)
            y -= 15

        y -= 20

    p.showPage()
    p.save()
    return response
