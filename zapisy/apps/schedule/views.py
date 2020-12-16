from datetime import datetime

from django.http import JsonResponse
from django.template.response import TemplateResponse

from apps.schedule.models.term import Term
from apps.enrollment.courses.models.classroom import Classroom



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


# TODO: normal user cannot see other people unaccepted events, he sees unaccepted self created events
#  Admin can see others unaccepted events

def events(request):
    type = request.GET.get('type', '2')
    status = request.GET.get('status', '1')
    visible = bool(request.GET.get('visible', True))
    room = request.GET.get('room', '')
    start = datetime.strptime(request.GET.get('start'), '%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.strptime(request.GET.get('end'), '%Y-%m-%dT%H:%M:%S.%fZ')

    query = Term.objects.filter(day__range=[start, end]).select_related('event')
    room = Classroom.objects.filter(number=room).first() if room else None
    if room:
        query = query.filter(room=room)
    if type:
        query = query.filter(event__type=type)
    if visible:
        query = query.filter(event__visible=visible)
    if status:
        query = query.filter(event__status=status)

    payload = []
    for term in query:
        event = term.event
        payload.append({"title": event.title,
                        "description": event.description,
                        "type": event.type,
                        "visible": event.visible,
                        "start": datetime.combine(term.day, term.start).isoformat(),
                        "end": datetime.combine(term.day, term.end).isoformat()})
    return JsonResponse(payload, safe=False)
