import json
from datetime import datetime

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from django.core.validators import ValidationError
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from apps.schedule.models.term import Term
from apps.schedule.models.event import Event
from apps.enrollment.courses.models.classroom import Classroom
from apps.users.models import Student, is_employee


def calendar(request):
    room = None
    rooms = Classroom.get_in_institute(reservation=True)
    return TemplateResponse(request, 'schedule/calendar.html', locals())


def report(request):
    return TemplateResponse(request, 'schedule/report.html', locals())


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
        statuses = request.GET.get('statuses', [])
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
        return HttpResponseBadRequest('Przesłane dane są nieprawidłowe lub niewystarczające')


# TODO: Ask if 403 vs 500 response, ValidationError is 500, 403 == Forbidden -- choose 400 errors, 500 will log it on slack and break server - huge error
# TODO: json payload - check if logged user is author
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
        if not event._user_can_see_or_404(request.user):
            continue
        payload.append({"title": event.title,
                        "status": event.status,
                        "type": event.type,
                        "visible": event.visible,
                        "url": event.get_absolute_url(),
                        "user_is_author": False,
                        "start": datetime.combine(term.day, term.start).isoformat(),
                        "end": datetime.combine(term.day, term.end).isoformat()})
    return JsonResponse(payload, safe=False)


def _check_and_prepare_post_payload(request):
    """Check if payload has proper keys nad values for creating and updating events"""
    payload = json.loads(request.body)
    checked_payload = {}
    # TODO: change author to request.user
    checked_payload['author'] = User.objects.get(first_name='M_74', last_name='B_74')
    try:
        checked_payload['title'] = str(payload.get('title', ''))
        checked_payload['description'] = str(payload.get('description', ''))
        checked_payload['visible'] = bool(payload.get('visible', True))
        # TODO change to Event.STATUS_PENDING
        checked_payload['status'] = str(payload.get('status', Event.STATUS_ACCEPTED))
        if not any(checked_payload['status'] == s for s, _ in Event.STATUSES):
            raise ValueError
        checked_payload['type'] = str(payload.get('type', Event.TYPE_GENERIC))
        if not any(checked_payload['type'] == t for t, _ in Event.TYPES):
            raise ValueError
        terms = payload.get('terms', [])
        if not isinstance(terms, list):
            raise TypeError
        if not terms:
            raise ValueError
        # TODO use clean method from model
        for term in terms:
            if not isinstance(term, dict):
                raise TypeError
            term['start'] = datetime.strptime(term['start'], '%H:%M').time()
            term['end'] = datetime.strptime(term['end'], '%H:%M').time()
            term['day'] = datetime.strptime(term['day'], '%Y-%m-%d').date()
            if term['start'] >= term['end']:
                raise ValidationError(
                    message={'end': ['Koniec musi następować po początku']},
                    code='invalid'
                )
            if 'place' not in term and 'room' not in term:
                raise KeyError
            if 'room' in term and term['room']:
                room = get_object_or_404(Classroom, number=term['room'])
                if not room.can_reserve:
                    raise ValidationError(
                        message={'room': ['Ta sala nie jest przeznaczona do rezerwacji']},
                        code='invalid'
                    )
                term['room'] = room
            else:
                term['room'] = None
            # Only one of 'room' and 'place' can be set. One or both must be None.
            if term['room'] or not isinstance(term['place'], str):
                term['place'] = None
            else:
                term['place'] = term['place']
        checked_payload['terms'] = terms
        return checked_payload
    except (ValueError, TypeError, KeyError):
        return HttpResponseBadRequest('Przesłane dane są nieprawidłowe lub niewystarczające')


def _authorize_user_can_create_update_event(payload, user, event_author=None):
    """Return tuple (True, None) if user can create or update event. Return (False, HttpResponseForbidden) otherwise"""
    if user.has_perm('schedule.manage_events'):
        return True, None
    if payload['author'] != user or (event_author and event_author != user):
        return False, HttpResponseForbidden('Nie można tworzyć lub zmieniać wydarzeń nie będąc ich autorem')
    if user.student:
        if payload['type'] != Event.TYPE_GENERIC:
            return False, HttpResponseForbidden('Nie masz uprawnień aby dodawać wydarzenia tego typu')
        if payload['status'] != Event.STATUS_PENDING:
            return False, HttpResponseForbidden('Nie masz uprawnień aby dodawać zaakceptowane wydarzenia')
    # Employee can create accepted exam and test events
    if user.employee:
        if payload['type'] not in Event.TYPES_FOR_TEACHER:
            return False, HttpResponseForbidden('Nie masz uprawnień aby dodawać wydarzenia tego typu')
        if payload['type'] == Event.TYPE_GENERIC and payload['status'] != Event.STATUS_PENDING:
            return False, HttpResponseForbidden('Nie masz uprawnień aby dodawać zaakceptowane wydarzenia')
    return True, None


def _get_event_author_url(author):
    if not author:
        return ""
    if is_employee(author):
        author_url = reverse('employee-profile', args=[author.pk])
    else:
        author_url = reverse('student-profile', args=[author.pk])
    return author_url


# Return list of conflicting terms without own terms
@csrf_exempt
def check_conflicts(request):
    payload = _check_and_prepare_post_payload(request)
    terms_conflicts = set()
    with transaction.atomic():
        event = Event.objects.create(title=payload['title'], author=payload['author'],
                                     description=payload['description'],
                                     type=payload['type'], visible=payload['visible'], status=payload['status'])
        for term in payload['terms']:
            term_conflicts = Term.objects.create(event=event, day=term["day"], start=term["start"], end=term["end"],
                                                 room=term["room"], place=term["place"]).get_conflicted()
            for conflict in term_conflicts:
                terms_conflicts.add(conflict)
        transaction.set_rollback(True)
    payload = []
    for term in terms_conflicts:
        payload.append({"title": term.event.title,
                        "description": term.event.description,
                        "author": term.event.author.get_full_name() if event.author else None,
                        "author_url": _get_event_author_url(term.event.author),
                        "status": term.event.status,
                        "type": term.event.type,
                        "visible": term.event.visible,
                        "url": term.event.get_absolute_url(),
                        "start": term.start,
                        "end": term.end,
                        "day": term.day,
                        "room": term.room.number if term.room else None,
                        "place": term.place})
    return JsonResponse(payload, safe=False)


# gets json, same structure like in GET
@csrf_exempt
@transaction.atomic
def create_event(request):
    payload = _check_and_prepare_post_payload(request)
    # TODO: User.objects.get to request.user
    authorized, http_response_forbidden = _authorize_user_can_create_update_event(payload,
                                                                                  User.objects.get(first_name='M_74',
                                                                                                   last_name='B_74'))
    if not authorized:
        return http_response_forbidden
    event = Event.objects.create(title=payload['title'], author=payload['author'], description=payload['description'],
                                 type=payload['type'], visible=payload['visible'], status=payload['status'])
    for term in payload['terms']:
        Term.objects.create(event=event, day=term["day"], start=term["start"],
                            end=term["end"], room=term["room"], place=term["place"])
    terms = event.term_set.all().select_related('room')
    if event.get_conflicted():
        terms_conflicts = set()
        for term in terms:
            term_conflicts = term.get_conflicted()
            for conflict in term_conflicts:
                terms_conflicts.add(conflict)
        payload = []
        for term in terms_conflicts:
            payload.append({"title": term.event.title,
                            "description": term.event.description,
                            "author": term.event.author.get_full_name() if event.author else None,
                            "author_url": _get_event_author_url(term.event.author),
                            "status": term.event.status,
                            "type": term.event.type,
                            "visible": term.event.visible,
                            "url": term.event.get_absolute_url(),
                            "start": term.start,
                            "end": term.end,
                            "day": term.day,
                            "room": term.room.number if term.room else None,
                            "place": term.place})
        transaction.set_rollback(True)
        return JsonResponse(payload, safe=False, status=400)
    return JsonResponse({"emails": list(event.get_followers()),
                         "terms": [{"start": t.start,
                                    "end": t.end,
                                    "day": t.day,
                                    "room": t.room.number if t.room else None,
                                    "place": t.place} for t in terms],
                         "description": event.description,
                         "author": event.author.get_full_name() if event.author else None,
                         "author_url": _get_event_author_url(event.author),
                         "title": event.title,
                         "status": event.status,
                         "type": event.type,
                         "visible": event.visible,
                         "url": event.get_absolute_url()}, status=201)


@csrf_exempt
@transaction.atomic
def update_event(request, event_id):
    payload = _check_and_prepare_post_payload(request)
    event = get_object_or_404(Event, pk=event_id)
    # TODO: User.objects.get to request.user
    authorized, http_response_forbidden = _authorize_user_can_create_update_event(payload,
                                                                                  User.objects.get(first_name='M_74',
                                                                                                   last_name='B_74'),
                                                                                  event_author=event.author)
    if not authorized:
        return http_response_forbidden
    event.title = payload['title']
    event.description = payload['description']
    event.type = payload['type']
    event.visible = payload['visible']
    event.status = payload['status']
    event.save()
    for payload_term in payload['terms']:
        payload_term['matched'] = False
    terms = event.term_set.all().select_related('room')
    for term in terms:
        matched = False
        # Check if term from event before changes is in new term list, if found do nothing, delete otherwise
        for payload_term in payload['terms']:
            if term.room is not payload_term['room'] or term.place != payload_term['place']:
                continue
            if term.day != payload_term['day']:
                continue
            if term.start != payload_term['start'] or term.end != payload_term['end']:
                continue
            matched = True
            payload_term['matched'] = True
            break
        if not matched:
            term.delete()
    # If term from new term list is not matched with actual terms, create this term
    for payload_term in payload['terms']:
        if not payload_term['matched']:
            Term.objects.create(event=event, day=payload_term["day"], start=payload_term["start"],
                                end=payload_term["end"], room=payload_term["room"], place=payload_term["place"])
    terms = event.term_set.all().select_related('room')
    if event.get_conflicted():
        terms_conflicts = set()
        for term in terms:
            term_conflicts = term.get_conflicted()
            for conflict in term_conflicts:
                terms_conflicts.add(conflict)
        payload = []
        for term in terms_conflicts:
            payload.append({"title": term.event.title,
                            "description": term.event.description,
                            "author": term.event.author.get_full_name() if event.author else None,
                            "author_url": _get_event_author_url(term.event.author),
                            "status": term.event.status,
                            "type": term.event.type,
                            "visible": term.event.visible,
                            "url": term.event.get_absolute_url(),
                            "start": term.start,
                            "end": term.end,
                            "day": term.day,
                            "room": term.room.number if term.room else None,
                            "place": term.place})
        transaction.set_rollback(True)
        return JsonResponse(payload, safe=False, status=400)
    return JsonResponse({"emails": list(event.get_followers()),
                         "terms": [{"start": t.start,
                                    "end": t.end,
                                    "day": t.day,
                                    "room": t.room.number if t.room else None,
                                    "place": t.place} for t in terms],
                         "description": event.description,
                         "author": event.author.get_full_name() if event.author else None,
                         "author_url": _get_event_author_url(event.author),
                         "title": event.title,
                         "status": event.status,
                         "type": event.type,
                         "visible": event.visible,
                         "url": event.get_absolute_url()}, status=201)


# TODO: time filtering or semester filtering. Add sorting by created or edited date if necessary
# TODO: event pagination, so client can get only necessary events for current page
@csrf_exempt
def events(request):
    if request.method == "POST":
        return create_event(request)
    data = _check_and_prepare_get_data(request)
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
        if not event._user_can_see_or_404(request.user):
            continue
        terms = event.term_set.all().select_related('room')
        author = event.author
        if is_employee(author):
            author_url = reverse('employee-profile', args=[author.pk])
        else:
            author_url = reverse('student-profile', args=[author.pk])
            student = Student.objects.get(user=author)
            if not student.consent_granted() and not request.user.employee:
                author = None
                author_url = None
        payload.append({"emails": list(event.get_followers()),
                        "terms": [{"start": t.start,
                                   "end": t.end,
                                   "day": t.day,
                                   "room": t.room.number if t.room else None,
                                   "place": t.place} for t in terms],
                        "description": event.description,
                        "author": author.get_full_name() if author else None,
                        "author_url": author_url,
                        "title": event.title,
                        "status": event.status,
                        "type": event.type,
                        "visible": event.visible,
                        "url": event.get_absolute_url()})
    return JsonResponse(payload, safe=False)


@csrf_exempt
def delete_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    # TODO: User.objects.get to request.user
    if not request.user.has_perm('schedule.manage_events') and event.author != User.objects.get(first_name='M_74',
                                                                                                last_name='B_74'):
        return HttpResponseForbidden('Nie można usuwać wydarzeń nie będąc ich autorem')
    event.delete()
    return HttpResponse("Event deleted", status=200)


@csrf_exempt
def event(request, event_id):
    if request.method == "POST":
        return update_event(request, event_id)
    event = Event.get_event_or_404(event_id, request.user)
    terms = event.term_set.all().select_related('room')
    author = event.author
    if is_employee(author):
        author_url = reverse('employee-profile', args=[author.pk])
    else:
        author_url = reverse('student-profile', args=[author.pk])
        student = Student.objects.get(user=author)
        if not student.consent_granted() and not request.user.employee:
            author = None
            author_url = None
    return JsonResponse({"emails": list(event.get_followers()),
                         "terms": [{"start": t.start,
                                    "end": t.end,
                                    "day": t.day,
                                    "room": t.room.number if t.room else None,
                                    "place": t.place} for t in terms],
                         "description": event.description,
                         "author": author.get_full_name() if author else None,
                         "author_url": author_url,
                         "title": event.title,
                         "status": event.status,
                         "type": event.type,
                         "visible": event.visible,
                         "url": event.get_absolute_url(), })
