import sys
from datetime import datetime

from django.http import JsonResponse
from django.template.response import TemplateResponse

from apps.schedule.models.term import Term
from apps.schedule.models.event import Event
from apps.enrollment.courses.models.classroom import Classroom


def calendar(request):
    room = None
    rooms = Classroom.get_in_institute(reservation=True)
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


# TODO make url, return similar data to /events/ ,but with rooms
def exams(request):
    pass


# TODO: normal user cannot see other people unaccepted events, he sees unaccepted self created events
#  Admin can see others unaccepted events
def events(request):
    type = request.GET.get('type', '2')
    status = request.GET.get('status', '1')
    visible = bool(request.GET.get('visible', True))
    room = request.GET.get('room', '')
    place = request.GET.get('place', '')
    start = datetime.strptime(request.GET.get('start'), '%Y-%m-%dT%H:%M:%S.%fZ')
    end = datetime.strptime(request.GET.get('end'), '%Y-%m-%dT%H:%M:%S.%fZ')

    query = Term.objects.filter(day__range=[start, end]).select_related('event')
    room = Classroom.objects.filter(number=room).first() if room else None
    if room:
        query = query.filter(room=room)
    if place:
        query = query.filter(place=place)
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
                        "status": event.status,
                        "type": event.type,
                        "visible": event.visible,
                        "url": event.get_absolute_url(),
                        "start": datetime.combine(term.day, term.start).isoformat(),
                        "end": datetime.combine(term.day, term.end).isoformat()})
    return JsonResponse(payload, safe=False)


def event(request, event_id):
    event = Event.get_event_or_404(event_id, request.user)
    terms = event.term_set.all().select_related('room')
    author = event.author
    # TODO get author url, how to check if user is student or employee?
    author_url = ""
    return JsonResponse({"emails": list(event.get_followers()),
                         "terms": [{"start": t.start,
                                    "end": t.end,
                                    "day:": t.day,
                                    "room": t.room.number,
                                    # TODO fix this to show proper url, not just /classrooms/ (main callendar without room filtering)
                                    # TODO look into room model implementation for TODO there
                                    "room_url": t.room.get_absolute_url(),
                                    "place": t.place} for t in terms],
                         "description": event.description,
                         "author": author.get_full_name(),
                         "author_url": author_url,
                         "title": event.title,
                         "status": event.status,
                         "type": event.type,
                         "visible": event.visible,
                         "url": event.get_absolute_url(), })
