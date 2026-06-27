from django.urls import path
from .views import login_view, logout_view
from .views import (
    dashboard,
    recognize_face,
    attendance_report,
    attendance_percentage,
    export_attendance,
    monthly_attendance,
    attendance_history
)

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    path('recognize/', recognize_face),
    path('report/', attendance_report),
    path('percentage/', attendance_percentage),
    path('export/', export_attendance),
    path("monthly/", monthly_attendance, name="monthly_attendance"),
    path("history/", attendance_history, name="attendance_history"),
]