from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Count, Case, When, IntegerField
from .models import Student, Teacher, Subject, Attendance, Timetable, User
from django.contrib.auth import authenticate, login as auth_login
from .forms import StudentForm, TeacherForm, AttendanceForm, LoginForm, SubjectForm, TimetableForm
from datetime import date, timedelta

def login_view(request):
    form = LoginForm()
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_roll = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Try as username first
            user = authenticate(request, username=username_or_roll, password=password)
            
            # If failed, try as roll number (if user is student)
            if user is None:
                student = Student.objects.filter(roll_number=username_or_roll).first()
                if student:
                    user = authenticate(request, username=student.user.username, password=password)
            
            if user is not None:
                auth_login(request, user)
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid username/roll number or password.")
                
    return render(request, 'attendance/login.html', {'form': form})

def is_admin(user):
    return user.role == 'admin'

@login_required
def dashboard(request):
    if request.user.role == 'admin':
        return admin_dashboard(request)
    elif request.user.role == 'teacher':
        return teacher_dashboard(request)
    elif request.user.role == 'student':
        return student_dashboard(request)
    return render(request, 'attendance/dashboard.html')

@login_required
@user_passes_test(is_admin)
def student_list(request):
    students = Student.objects.all().select_related('user')
    search_query = request.GET.get('q')
    if search_query:
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(class_name__icontains=search_query)
        )
    return render(request, 'attendance/student_list.html', {'students': students})

@login_required
@user_passes_test(is_admin)
def student_add(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Student added successfully!')
            return redirect('student_list')
    else:
        form = StudentForm()
    return render(request, 'attendance/student_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def student_update(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student, initial={
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
            'username': student.user.username,
        })
        if form.is_valid():
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('student_list')
    else:
        form = StudentForm(instance=student, initial={
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
            'username': student.user.username,
        })
    return render(request, 'attendance/student_form.html', {'form': form, 'student': student})

@login_required
@user_passes_test(is_admin)
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    user = student.user
    student.delete()
    user.delete()
    messages.success(request, 'Student deleted successfully!')
    return redirect('student_list')

@login_required
@user_passes_test(is_admin)
def teacher_list(request):
    teachers = Teacher.objects.all().select_related('user')
    search_query = request.GET.get('q')
    if search_query:
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__username__icontains=search_query) |
            Q(phone__icontains=search_query)
        )
    return render(request, 'attendance/teacher_list.html', {'teachers': teachers})

@login_required
@user_passes_test(is_admin)
def teacher_add(request):
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher added successfully!')
            return redirect('teacher_list')
    else:
        form = TeacherForm()
    return render(request, 'attendance/teacher_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def teacher_update(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher, initial={
            'first_name': teacher.user.first_name,
            'last_name': teacher.user.last_name,
            'email': teacher.user.email,
            'username': teacher.user.username,
        })
        if form.is_valid():
            form.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('teacher_list')
    else:
        form = TeacherForm(instance=teacher, initial={
            'first_name': teacher.user.first_name,
            'last_name': teacher.user.last_name,
            'email': teacher.user.email,
            'username': teacher.user.username,
        })
    return render(request, 'attendance/teacher_form.html', {'form': form, 'teacher': teacher})

@login_required
@user_passes_test(is_admin)
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    user = teacher.user
    teacher.delete()
    user.delete()
    messages.success(request, 'Teacher deleted successfully!')
    return redirect('teacher_list')

def admin_dashboard(request):
    total_students = Student.objects.count()
    total_teachers = Teacher.objects.count()
    total_subjects = Subject.objects.count()
    
    # Calculate today's attendance summary
    today = date.today()
    attendance_today = Attendance.objects.filter(date=today)
    total_marked = attendance_today.count()
    present_today = attendance_today.filter(status='Present').count()
    absent_today = total_marked - present_today
    
    attendance_percentage = (present_today / total_marked * 100) if total_marked > 0 else 0
    
    # Last 7 days attendance trend
    labels = []
    trend_data = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        labels.append(day.strftime('%a'))
        day_attendance = Attendance.objects.filter(date=day)
        day_total = day_attendance.count()
        day_present = day_attendance.filter(status='Present').count()
        day_percent = (day_present / day_total * 100) if day_total > 0 else 0
        trend_data.append(day_percent)

    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'attendance_percentage': round(attendance_percentage, 1),
        'absent_today': absent_today,
        'labels': labels,
        'trend_data': trend_data,
    }
    return render(request, 'attendance/admin_dashboard.html', context)

def teacher_dashboard(request):
    teacher = request.user.teacher
    subjects = Subject.objects.filter(teacher=teacher)
    
    # Get attendance stats for each subject
    subject_stats = []
    for subject in subjects:
        attendance = Attendance.objects.filter(subject=subject)
        total = attendance.count()
        present = attendance.filter(status='Present').count()
        percent = (present / total * 100) if total > 0 else 0
        subject_stats.append({
            'subject': subject,
            'percent': round(percent, 1),
            'total': total
        })
        
    context = {
        'subject_stats': subject_stats,
    }
    return render(request, 'attendance/teacher_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def subject_list(request):
    subjects = Subject.objects.all().select_related('teacher__user')
    return render(request, 'attendance/subject_list.html', {'subjects': subjects})

@login_required
@user_passes_test(is_admin)
def subject_add(request):
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully!')
            return redirect('subject_list')
    else:
        form = SubjectForm()
    return render(request, 'attendance/subject_form.html', {'form': form})

@login_required
@user_passes_test(is_admin)
def subject_update(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    if request.method == 'POST':
        form = SubjectForm(request.POST, instance=subject)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject updated successfully!')
            return redirect('subject_list')
    else:
        form = SubjectForm(instance=subject)
    return render(request, 'attendance/subject_form.html', {'form': form, 'subject': subject})

@login_required
@user_passes_test(is_admin)
def subject_delete(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    messages.success(request, 'Subject deleted successfully!')
    return redirect('subject_list')

@login_required
def timetable_list(request):
    if request.user.role == 'student':
        student = request.user.student
        branch = student.branch
        section = student.section
        semester = student.semester
    else:
        branch = request.GET.get('branch')
        section = request.GET.get('section')
        semester = request.GET.get('semester')

    timetables = Timetable.objects.all().select_related('subject', 'teacher__user')
    
    if branch:
        timetables = timetables.filter(branch=branch)
    if section:
        timetables = timetables.filter(section=section)
    if semester:
        timetables = timetables.filter(semester=semester)

    # Organize into a list of rows for the template (no custom filter needed)
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    hours = range(1, 9)
    
    timetable_grid = []
    for day in days:
        row = {'day': day, 'slots': []}
        for hour in hours:
            entry = timetables.filter(day=day, hour=hour).first()
            row['slots'].append(entry)
        timetable_grid.append(row)

    context = {
        'timetable_grid': timetable_grid,
        'hours': hours,
        'branch': branch,
        'section': section,
        'semester': semester,
    }
    return render(request, 'attendance/timetable_list.html', context)

@login_required
@user_passes_test(is_admin)
def timetable_add(request):
    if request.method == 'POST':
        form = TimetableForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Timetable entry added successfully!')
            return redirect('timetable_list')
    else:
        form = TimetableForm()
    return render(request, 'attendance/timetable_form.html', {'form': form})


@login_required
def attendance_reports(request):
    report_type = request.GET.get('report_type', 'daily')
    month = request.GET.get('month')
    semester = request.GET.get('semester')
    
    if request.user.role == 'student':
        student = request.user.student
        attendance = Attendance.objects.filter(student=student).select_related('subject', 'teacher__user')
        
        if report_type == 'monthly' and month:
            attendance = attendance.filter(date__month=month)
        elif report_type == 'semester' and semester:
            attendance = attendance.filter(student__semester=semester)
            
    elif request.user.role == 'teacher':
        teacher = request.user.teacher
        attendance = Attendance.objects.filter(teacher=teacher).select_related('student__user', 'subject')
        
        if report_type == 'monthly' and month:
            attendance = attendance.filter(date__month=month)
    else:
        attendance = Attendance.objects.all().select_related('student__user', 'subject', 'teacher__user')

    context = {
        'attendance': attendance,
        'report_type': report_type,
        'months': range(1, 13),
    }
    return render(request, 'attendance/reports.html', context)

def student_dashboard(request):
    student = request.user.student
    attendance_data = Attendance.objects.filter(student=student).values('subject__name').annotate(
        present_count=Count(Case(When(status='Present', then=1), output_field=IntegerField())),
        total_count=Count('id')
    )
    
    subjects = [item['subject__name'] for item in attendance_data]
    percentages = [
        (item['present_count'] / item['total_count'] * 100) if item['total_count'] > 0 else 0 
        for item in attendance_data
    ]
    
    context = {
        'student': student,
        'subjects': subjects,
        'percentages': percentages,
    }
    return render(request, 'attendance/student_dashboard.html', context)



def student_register(request):
    if request.method == "POST":
        form = StudentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Student registered successfully")
            return redirect("login")
    else:
        form = StudentForm()
    return render(request, "attendance/student_register.html", {'form': form})

def teacher_register(request):
    if request.method == "POST":
        form = TeacherForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Teacher registered successfully")
            return redirect("login")
    else:
        form = TeacherForm()
    return render(request, "attendance/teacher_register.html", {'form': form})


def is_admin_or_teacher(user):
    return user.role in ['admin', 'teacher']

@login_required
@user_passes_test(is_admin_or_teacher)
def mark_attendance(request):
    if request.user.role == 'teacher':
        teacher = request.user.teacher
        subjects = Subject.objects.filter(teacher=teacher)
    else:
        teacher = None
        subjects = Subject.objects.all()

    students = []
    class_name = request.GET.get('class_name')
    branch = request.GET.get('branch')
    section = request.GET.get('section')
    semester = request.GET.get('semester')
    subject_id = request.GET.get('subject')
    hour = request.GET.get('hour')
    date_val = request.GET.get('date', date.today().strftime('%Y-%m-%d'))

    if branch and section and semester:
        students = Student.objects.filter(branch=branch, section=section, semester=semester)

    if request.method == "POST":
        subject_id = request.POST.get("subject")
        hour = request.POST.get("hour")
        date_str = request.POST.get("date")
        date_obj = date.fromisoformat(date_str) if date_str else date.today()
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Re-fetch students for POST processing
        p_branch = request.POST.get("branch")
        p_section = request.POST.get("section")
        p_semester = request.POST.get("semester")
        if p_branch and p_section and p_semester:
            students = Student.objects.filter(branch=p_branch, section=p_section, semester=p_semester)
        
        # If teacher is marking, ensure it's their subject
        if request.user.role == 'teacher' and subject.teacher != request.user.teacher:
            messages.error(request, "You are not authorized to mark attendance for this subject.")
            return redirect('mark_attendance')

        for student in students:
            status = request.POST.get(f'status_{student.id}')
            if status:
                Attendance.objects.update_or_create(
                    student=student,
                    subject=subject,
                    date=date_obj,
                    hour=hour,
                    defaults={'status': status, 'teacher': subject.teacher}
                )

        messages.success(request, "Attendance marked successfully")
        return redirect("dashboard")

    context = {
        "students": students,
        "subjects": subjects,
        "class_name": class_name,
        "branch": branch,
        "section": section,
        "semester": semester,
        "subject_id": subject_id,
        "hour": hour,
        "date": date_val,
    }

    return render(request, "attendance/mark_attendance.html", context)