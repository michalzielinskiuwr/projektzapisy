from datetime import datetime
from apps.enrollment.courses.models.semester import Semester
from apps.schedule.models.term import Term
from apps.schedule.models.event import Event
from django.contrib.auth.models import User

current_year = '2020/21'
next_year = '2020/21'
semester_type = 'z'

def run():
    reservations = Event.objects.filter(type=Event.TYPE_SPECIAL_RESERVATION)
    semester = Semester.objects.get(
        year=next_year,
        type=semester_type)
    for reservation in reservations:
        print(reservation)
        if input('Confirm (Y/n):') != 'n':
            new_event = Event()
            new_event.title = reservation.title
            new_event.description = reservation.description
            new_event.type = Event.TYPE_SPECIAL_RESERVATION
            new_event.visible = True
            new_event.status = Event.STATUS_ACCEPTED
            new_event.author_id = User.objects.get(username='asm').id
            new_event.save()

            term_days = semester.get_all_days_of_week(
                day_of_week=reservation.dayOfWeek, start_date=semester.lectures_beginning)

            for day in term_days:
                term = Term()
                term.event = new_event
                term.day = day
                term.start = reservation.start_time
                term.end = reservation.end_time
                term.room = reservation.classroom
                term.save()