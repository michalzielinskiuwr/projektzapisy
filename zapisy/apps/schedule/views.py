from datetime import datetime, timedelta

from django.http import JsonResponse
from django.template.response import TemplateResponse

from apps.schedule.models.term import Term


def calendar(request):
    return TemplateResponse(request, 'schedule/calendar.html', locals())


def calendar_admin(request):
    return TemplateResponse(request, 'schedule/calendar_admin.html', locals())


def history(request):
    return TemplateResponse(request, 'schedule/history.html', locals())


def report(request):
    return TemplateResponse(request, 'schedule/report.html', locals())


def reservation(request):
    return TemplateResponse(request, 'schedule/reservation.html', locals())


def session(request):
    return TemplateResponse(request, 'schedule/session.html', locals())


def events(request):
    sdate = datetime(2020, 10, 1).date()  # start date
    edate = datetime(2021, 2, 28).date()  # end date

    delta = edate - sdate
    days = []

    for i in range(delta.days + 1):
        day = sdate + timedelta(days=i)
        days.append(day)

    query = Term.objects.filter(day__in=days, event__type="2").select_related('event')
    payload = []
    for term in query:
        payload.append({"title":    term.event.title,
                        "start":    datetime.combine(term.day, term.start).isoformat(),
                        "end":      datetime.combine(term.day, term.end).isoformat()})
    return JsonResponse(payload, safe=False)
