from datetime import datetime

from django.db.models import Q
from django.http import JsonResponse, Http404
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


# TODO check if events is enough to replace exams function
# TODO make url, return similar data to /events/ ,but with rooms
def exams(request):
    pass


# TODO: normal user cannot see other people unaccepted events, he sees unaccepted self created events
#  Admin can see others unaccepted events
# Sends only required data for fullcalendar
def terms(request):
    # GET parameters checking
    try:
        start = datetime.strptime(request.GET.get('start'), '%Y-%m-%dT%H:%M:%S.%fZ')
        end = datetime.strptime(request.GET.get('end'), '%Y-%m-%dT%H:%M:%S.%fZ')
        visible = bool(request.GET.get('visible', True))
        place = str(request.GET.get('place', ''))
        title_or_author = str(request.GET.get('title_author', ''))
        types = request.GET.get('types', [Event.TYPE_GENERIC])
        types = types.split(',') if isinstance(types, str) else types
        if not isinstance(types, list):
            raise ValueError
        for type_ in types:
            if not any(type_ == t for t, _ in Event.TYPES):
                raise ValueError
        statuses = request.GET.get('statuses', [Event.STATUS_ACCEPTED])
        statuses = statuses.split(',') if isinstance(statuses, str) else statuses
        if not isinstance(statuses, list):
            raise ValueError
        for status in statuses:
            if not any(status == s for s, _ in Event.STATUSES):
                raise ValueError
        rooms = request.GET.get('rooms', [])
        rooms = rooms.split(',') if rooms else rooms
        if not isinstance(rooms, list):
            raise ValueError
        for room in rooms:
            if not isinstance(room, str):
                raise ValueError
    except (ValueError, TypeError):
        raise Http404

    query = Term.objects.filter(day__range=[start, end]).select_related('event')
    rooms = Classroom.objects.filter(number__in=rooms) if rooms else None
    if rooms:
        query = query.filter(room__in=rooms)
    if place:
        query = query.filter(place=place)
    if types:
        query = query.filter(event__type__in=types)
    if visible:
        query = query.filter(event__visible=visible)
    if statuses:
        query = query.filter(event__status__in=statuses)
    if title_or_author:
        author_names = title_or_author.split()
        first_name = author_names[0]
        last_name = author_names[-1]
        query = query.filter(Q(event__title__icontains=title_or_author) |
                             Q(event__author__first_name__icontains=first_name) |
                             Q(event__author__first_name__icontains=last_name) |
                             Q(event__author__last_name__icontains=first_name) |
                             Q(event__author__last_name__icontains=last_name))

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


# TODO: time filtering or semester filtering. Add sorting by created or edited date if necessary
# TODO: event pagination, so client can get only necessary events for current page
# TODO: normal user cannot see other people unaccepted events, he sees unaccepted self created events
#  Admin can see others unaccepted events
def events(request):
    # GET parameters checking
    try:
        visible = bool(request.GET.get('visible', True))
        title_or_author = str(request.GET.get('title_author', ''))
        types = request.GET.get('types', [Event.TYPE_GENERIC])
        types = types.split(',') if isinstance(types, str) else types
        if not isinstance(types, list):
            raise ValueError
        for type in types:
            if not any(type == t for t, _ in Event.TYPES):
                raise ValueError
        statuses = request.GET.get('statuses', [Event.STATUS_ACCEPTED])
        statuses = statuses.split(',') if isinstance(statuses, str) else statuses
        if not isinstance(statuses, list):
            raise ValueError
        for status in statuses:
            if not any(status == s for s, _ in Event.STATUSES):
                raise ValueError
    except (ValueError, TypeError):
        raise Http404

    # TODO: events filtering, similar to Event.get_event_or_404(event_id, request.user) but for many events,
    query = Event.objects.filter().select_related('author')
    if types:
        query = query.filter(type__in=types)
    if visible:
        query = query.filter(visible=visible)
    if statuses:
        query = query.filter(status__in=statuses)
    if title_or_author:
        author_names = title_or_author.split()
        first_name = author_names[0]
        last_name = author_names[-1]
        query = query.filter(Q(title__icontains=title_or_author) |
                             Q(author__first_name__icontains=first_name) |
                             Q(author__first_name__icontains=last_name) |
                             Q(author__last_name__icontains=first_name) |
                             Q(author__last_name__icontains=last_name))

    payload = []
    for event in query:
        terms = event.term_set.all().select_related('room')
        author = event.author
        # TODO get author url, how to check if user is student or employee?
        author_url = ""
        payload.append({"emails": list(event.get_followers()),
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
                        "url": event.get_absolute_url()})
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
