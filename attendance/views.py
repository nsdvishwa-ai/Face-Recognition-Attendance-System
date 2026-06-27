import cv2
import json
import face_recognition
import openpyxl

from datetime import date

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.utils.safestring import mark_safe

from .models import Employee, Attendance, MonthlyWorkingDays


@login_required(login_url='/login/')
def dashboard(request):
    total_employees = Employee.objects.count()

    today_attendance = Attendance.objects.filter(date=date.today()).count()
    absent_employees = total_employees - today_attendance

    chart_data = {
        "present": today_attendance,
        "absent": absent_employees
    }

    return render(request, 'attendance/dashboard.html', {
        'total_employees': total_employees,
        'today_attendance': today_attendance,
        'absent_employees': absent_employees,
        'chart_data': mark_safe(json.dumps(chart_data))
    })
def recognize_face(request):
    video = cv2.VideoCapture(0)

    if not video.isOpened():
        return HttpResponse("Camera not found")

    captured_frame = None

    try:
        while True:
            ret, frame = video.read()

            if not ret:
                return HttpResponse("Unable to read from camera")

            cv2.imshow("Mark Attendance - Press Enter to Capture, Esc to Cancel", frame)

            key = cv2.waitKey(1) & 0xFF

            # Esc key cancels attendance
            if key == 27:
                return HttpResponse("Attendance cancelled")

            # Enter key captures current frame
            if key == 13 or key == 10:
                captured_frame = frame.copy()
                break

        if captured_frame is None:
            return HttpResponse("No frame captured")

        rgb_frame = cv2.cvtColor(captured_frame, cv2.COLOR_BGR2RGB)

        faces = face_recognition.face_encodings(rgb_frame)

        if len(faces) == 0:
            return HttpResponse("No face detected")

        current_face = faces[0]

        employees = Employee.objects.all()

        for emp in employees:
            stored_encoding = json.loads(emp.face_encoding)

            match = face_recognition.compare_faces(
                [stored_encoding],
                current_face
            )[0]

            if match:
                today = date.today()

                already_marked = Attendance.objects.filter(
                    employee=emp,
                    date=today
                ).exists()

                if already_marked:
                    return HttpResponse(
                        f"Attendance already marked today for {emp.name}"
                    )

                Attendance.objects.create(
                    employee=emp
                )

                return HttpResponse(
                    f"Attendance Marked for {emp.name}"
                )

        return HttpResponse("Unknown Face")

    finally:
        video.release()
        cv2.destroyAllWindows()


def attendance_report(request):
    search_name = request.GET.get('name')
    search_date = request.GET.get('date')

    records = Attendance.objects.all()

    if search_name:
        records = records.filter(employee__name__icontains=search_name)

    if search_date:
        records = records.filter(date=search_date)

    records = records.order_by('-date', '-time')

    return render(request, 'attendance/report.html', {
        'records': records
    })


def attendance_percentage(request):
    employees = Employee.objects.all()

    data = []

    total_days = Attendance.objects.values('date').distinct().count()

    for emp in employees:
        present_days = Attendance.objects.filter(
            employee=emp
        ).values('date').distinct().count()

        percentage = 0

        if total_days > 0:
            percentage = round((present_days / total_days) * 100, 2)

        data.append({
            'employee': emp,
            'present_days': present_days,
            'total_days': total_days,
            'percentage': percentage
        })

    return render(request, 'attendance/percentage.html', {
        'data': data
    })

def monthly_attendance(request):
    employees = Employee.objects.all()
    data = []

    if request.method == "GET":
        employee_id = request.GET.get("employee")
        month = request.GET.get("month")
        year = request.GET.get("year")

        if employee_id and month and year:

            employee = Employee.objects.get(id=employee_id)

            present_days = Attendance.objects.filter(
                employee=employee,
                date__month=month,
                date__year=year
            ).count()

            working = MonthlyWorkingDays.objects.filter(
                month=month,
                year=year
            ).first()

            working_days = working.working_days if working else 0

            absent_days = max(working_days - present_days, 0)

            percentage = 0

            if working_days > 0:
                percentage = round((present_days / working_days) * 100, 2)

            data.append({
                "employee": employee,
                "working_days": working_days,
                "present_days": present_days,
                "absent_days": absent_days,
                "percentage": percentage,
            })

    return render(request, "attendance/monthly_attendance.html", {
        "employees": employees,
        "data": data
    })

def export_attendance(request):
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Attendance Report"

    sheet.append(["Employee Name", "Date", "Time"])

    records = Attendance.objects.all().order_by('-date', '-time')

    for record in records:
        sheet.append([
            record.employee.name,
            record.date.strftime("%Y-%m-%d"),
            record.time.strftime("%H:%M:%S")
        ])

    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=attendance_report.xlsx'

    workbook.save(response)

    return response


def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            return HttpResponse("Invalid credentials")

    return render(request, 'attendance/login.html')


def logout_view(request):
    logout(request)
    return redirect('login')
from datetime import date, timedelta

def attendance_history(request):

    employees = Employee.objects.all()

    history = []

    employee_id = request.GET.get("employee")
    month = request.GET.get("month")
    year = request.GET.get("year")

    if employee_id and month and year:

        employee = Employee.objects.get(id=employee_id)

        working = MonthlyWorkingDays.objects.filter(
            month=month,
            year=year
        ).first()

        if working:

            present_records = Attendance.objects.filter(
                employee=employee,
                date__month=month,
                date__year=year
            )

            present_dates = {}

            for record in present_records:

                present_dates[record.date] = record

            start_date = date(int(year), int(month), 1)

            count = 0

            current = start_date

            while count < working.working_days:

                if current in present_dates:

                    history.append({
                        "date": current,
                        "time": present_dates[current].time,
                        "status": "Present"
                    })

                else:

                    history.append({
                        "date": current,
                        "time": "-",
                        "status": "Absent"
                    })

                current += timedelta(days=1)

                count += 1

    return render(request,
                  "attendance/history.html",
                  {
                      "employees": employees,
                      "history": history
                  })