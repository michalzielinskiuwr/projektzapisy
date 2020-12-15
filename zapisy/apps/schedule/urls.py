from django.urls import path

from . import views

urlpatterns = [
    path('', views.calendar, name='calendar'),
    path('calendar-admin/', views.calendar_admin, name='calendar-admin'),
    path('history/', views.history, name='history'),
    path('report/', views.report, name='report'),
    path('reservation/', views.reservation, name='reservation'),
    path('session/', views.session, name='session'),
    path('events/', views.events, name="events")
]
