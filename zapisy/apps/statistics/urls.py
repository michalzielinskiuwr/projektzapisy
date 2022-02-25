from django.urls import path

from . import views

urlpatterns = [
    path('students/', views.students, name='students'),
    path('groups/', views.groups, name='groups'),
    path('overload/', views.overloads, name='overloads'),
]
