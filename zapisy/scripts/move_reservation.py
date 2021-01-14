import datetime
from apps.enrollment.courses.models.semester import Semester
from apps.schedule.models.specialreservation import SpecialReservation
from apps.schedule.models.term import Term
from apps.schedule.models.event import Event
from django.contrib.auth.models import User

current_year = '2020/21'

def offset(day, day_t):
    if day < day_t:
        return day - day_t + 7
    elif day > day_t :
        return day - day_t
    else:
        return 0

def run():
    reservations = SpecialReservation.objects.filter(
        semester__year=current_year)

    for reservation in reservations:

        new_event = Event(
            title=reservation.title,
            description='Rezerwacja stała',
            type = Event.TYPE_SPECIAL_RESERVATION,
            visible = True,
            status = Event.STATUS_ACCEPTED,
            author = User.objects.get(username='asm')
        )

        new_event.save()
        semester_start = reservation.semester.lectures_beginning
        semester_end = reservation.semester.lectures_ending


        off = offset(int(reservation.dayOfWeek), semester_start.weekday())
        semester_start += datetime.timedelta(days = off)
        while semester_start <= semester_end:
            new_term = Term(
                event= new_event,
                day= semester_start,
                start= reservation.start_time,
                end= reservation.end_time,
                room= reservation.classroom,
                place= reservation.title,
                ignore_conflicts= True
            )
            new_term.save()
            semester_start += datetime.timedelta(days=7)
