import json
from datetime import datetime

from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse, Http404, HttpResponseBadRequest, HttpResponse
from django.template.response import TemplateResponse
from django.core.exceptions import PermissionDenied
from django.views.decorators.csrf import csrf_exempt

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


def _check_and_prepare_get_data(request):
    data = {}
    try:
        data['start'] = datetime.strptime(request.GET.get('start'), '%Y-%m-%dT%H:%M:%S.%fZ')
        data['end'] = datetime.strptime(request.GET.get('end'), '%Y-%m-%dT%H:%M:%S.%fZ')
        data['visible'] = bool(request.GET.get('visible', True))
        data['place'] = str(request.GET.get('place', ''))
        data['title_or_author'] = str(request.GET.get('title_author', ''))
        types = request.GET.get('types', [Event.TYPE_GENERIC])
        types = types.split(',') if isinstance(types, str) else types
        if not isinstance(types, list):
            raise TypeError
        for type_ in types:
            if not any(type_ == t for t, _ in Event.TYPES):
                raise ValueError
        data['types'] = types
        statuses = request.GET.get('statuses', [Event.STATUS_ACCEPTED])
        statuses = statuses.split(',') if isinstance(statuses, str) else statuses
        if not isinstance(statuses, list):
            raise TypeError
        for status in statuses:
            if not any(status == s for s, _ in Event.STATUSES):
                raise ValueError
        data['statuses'] = statuses
        rooms = request.GET.get('rooms', [])
        rooms = rooms.split(',') if rooms else rooms
        if not isinstance(rooms, list):
            raise TypeError
        for room in rooms:
            if not isinstance(room, str):
                raise ValueError
        data['rooms'] = rooms
        return data
    except (ValueError, TypeError):
        raise Http404


# TODO: Ask if GET parameters checking is necessary. 404 vs 500 response
# TODO: normal user cannot see other people unaccepted events, he sees unaccepted self created events
#  Admin can see others unaccepted events
# Sends only required data for fullcalendar
def terms(request):
    data = _check_and_prepare_get_data(request)
    query = Term.objects.filter(day__range=[data['start'], data['end']]).select_related('event')
    rooms = Classroom.objects.filter(number__in=data['rooms']) if data['rooms'] else None
    if rooms:
        query = query.filter(room__in=rooms)
    if data['place']:
        query = query.filter(place=data['place'])
    if data['types']:
        query = query.filter(event__type__in=data['types'])
    if data['statuses']:
        query = query.filter(event__status__in=data['statuses'])
    if data['title_or_author']:
        author_names = data['title_or_author'].split()
        first_name = author_names[0]
        last_name = author_names[-1]
        query = query.filter(Q(event__title__icontains=data['title_or_author']) |
                             Q(event__author__first_name__icontains=first_name) |
                             Q(event__author__first_name__icontains=last_name) |
                             Q(event__author__last_name__icontains=first_name) |
                             Q(event__author__last_name__icontains=last_name))
    query = query.filter(event__visible=data['visible'])
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


def _check_and_prepare_post_payload(request):
    """Check if payload has proper keys nad values for creating and updating events"""
    payload = json.loads(request.body)
    checked_payload = {}
    # TODO: change author to request.user
    checked_payload['author'] = User.objects.get(first_name='M_74', last_name='B_74')
    # TODO: change Event status to STATUS_PENDING, STATUS_ACCEPTED should be only if author is admin?
    checked_payload['status'] = Event.STATUS_ACCEPTED
    try:
        checked_payload['title'] = str(payload.get('title', ''))
        checked_payload['description'] = str(payload.get('description', ''))
        checked_payload['visible'] = bool(payload.get('visible', True))
        checked_payload['type'] = payload.get('type', [Event.TYPE_GENERIC])
        if not any(checked_payload['type'] == t for t, _ in Event.TYPES):
            raise ValueError
        terms = payload.get('terms', [])
        if not isinstance(terms, list):
            raise TypeError
        if not terms:
            raise ValueError
        for term in terms:
            if not isinstance(term, dict):
                raise TypeError
            term['start'] = datetime.strptime(term['start'], '%Y-%m-%dT%H:%M:%S.%fZ')
            term['end'] = datetime.strptime(term['end'], '%Y-%m-%dT%H:%M:%S.%fZ')
            if term['start'].date() != term['end'].date():
                raise ValueError
            if not any(k in term for k in ('room', 'place')):
                raise KeyError
        checked_payload['terms'] = terms
        return checked_payload
    except (ValueError, TypeError, KeyError):
        raise Http404


# gets json, same structure like in GET
# TODO return url to new event?
# TODO: transaction atomic for creating Event and Terms
# TODO: Is creating normal class events required? Ask
@csrf_exempt
def create_event(request):
    payload = _check_and_prepare_post_payload(request)
    event = Event.objects.create(title=payload['title'], author=payload['author'], description=payload['description'],
                                 type=payload['type'], visible=payload['visible'], status=payload['status'])
    for term in payload['terms']:
        room = Classroom.objects.get(number=term['room']) if 'room' in term else None
        place = term['place'] if 'place' in term else None
        term = Term(event=event, day=term["start"].date(), start=term["start"].time(), end=term["end"].time())
        if room:
            term.room = room
        else:
            term.place = place
        term.save()
    # return HttpResponseBadRequest()
    return HttpResponse("<html><body>Event created</body></html>", status=201)


# TODO: time filtering or semester filtering. Add sorting by created or edited date if necessary
# TODO: event pagination, so client can get only necessary events for current page
# TODO: normal user cannot see other people unaccepted events, he sees unaccepted self created events
#  Admin can see others unaccepted events
@csrf_exempt
def events(request):
    if request.method == "POST":
        return create_event(request)
    data = _check_and_prepare_get_data(request)
    # TODO: events filtering, similar to Event.get_event_or_404(event_id, request.user) but for many events,
    query = Event.objects.filter().select_related('author')
    if data['types']:
        query = query.filter(type__in=data['types'])
    if data['statuses']:
        query = query.filter(status__in=data['statuses'])
    if data['title_or_author']:
        author_names = data['title_or_author'].split()
        first_name = author_names[0]
        last_name = author_names[-1]
        query = query.filter(Q(title__icontains=data['title_or_author']) |
                             Q(author__first_name__icontains=first_name) |
                             Q(author__first_name__icontains=last_name) |
                             Q(author__last_name__icontains=first_name) |
                             Q(author__last_name__icontains=last_name))
    query = query.filter(visible=data['visible'])
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
                                   "room": t.room.number if t.room else None,
                                   # TODO fix this to show proper url, not just /classrooms/ (main callendar without room filtering)
                                   # TODO look into room model implementation for TODO there
                                   "room_url": t.room.get_absolute_url() if t.room else None,
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


@csrf_exempt
def delete_event(request, event_id):
    Event.objects.get(pk=event_id).delete()
    return HttpResponse("<html><body>Event deleted</body></html>", status=200)


@csrf_exempt
def update_event(request, event_id):
    # TODO
    return HttpResponse("<html><body>Event updated</body></html>", status=200)


# TODO: normal user cannot see other people unaccepted events, he sees unaccepted self created events
#  Admin can see others unaccepted events
@csrf_exempt
def event(request, event_id):
    if request.method == "POST":
        return update_event(request, event_id)
    if request.method == "DELETE":
        return delete_event(request, event_id)
    event = Event.get_event_or_404(event_id, request.user)
    terms = event.term_set.all().select_related('room')
    author = event.author
    # TODO get author url, how to check if user is student or employee?
    author_url = ""
    return JsonResponse({"emails": list(event.get_followers()),
                         "terms": [{"start": t.start,
                                    "end": t.end,
                                    "day:": t.day,
                                    "room": t.room.number if t.room else None,
                                    # TODO fix this to show proper url, not just /classrooms/ (main callendar without room filtering)
                                    # TODO look into room model implementation for TODO there
                                    "room_url": t.room.get_absolute_url() if t.room else None,
                                    "place": t.place} for t in terms],
                         "description": event.description,
                         "author": author.get_full_name(),
                         "author_url": author_url,
                         "title": event.title,
                         "status": event.status,
                         "type": event.type,
                         "visible": event.visible,
                         "url": event.get_absolute_url(), })
