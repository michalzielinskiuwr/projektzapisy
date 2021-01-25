import copy
import json
import operator
from collections import defaultdict
from datetime import date, datetime, timedelta
from itertools import groupby
from typing import NamedTuple, Optional, List

from django import forms
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden, HttpResponseBadRequest, Http404
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.core.validators import ValidationError
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.schedule.models.term import Term
from apps.schedule.models.event import Event
from apps.enrollment.courses.models.classroom import Classroom, Floors
from apps.enrollment.courses.models.semester import Semester
from apps.enrollment.courses.models.term import Term as CourseTerm
from apps.users.models import Student, is_employee


@login_required
def calendar(request):
    room = None
    rooms = Classroom.get_in_institute(reservation=True)
    return TemplateResponse(request, 'schedule/calendar.html', locals())


def _check_and_prepare_get_data(request, require_dates=True):
    """ Cast GET query parameters to python objects.

        Args:
            request - GET request.
            require_dates - When function 'events' calls this method it does not need 'start' and 'end' in request
                            parameters.
        Returns:
            Dictionary with properly casted and validated python objects needed to filter Terms.
        Raises:
            ValidationError: If require_dates=True and request.GET doesn't have 'start' and 'end' key or
                                request.GET['start'] or request.GET['end'] don't cast to datetime with proper format.
                             If request.GET['statuses'] are not separated with comma Event.Statuses like "0,1" or empty.
                             If request.GET['types'] are not separated with comma Event.Types like "2,3" or empty.
    """
    data = {}
    try:
        if require_dates:
            data['start'] = datetime.strptime(request.GET.get('start'), '%Y-%m-%dT%H:%M:%S.%fZ')
            data['end'] = datetime.strptime(request.GET.get('end'), '%Y-%m-%dT%H:%M:%S.%fZ')
        data['page'] = int(request.GET.get('page', 1))
        visible = request.GET.get('visible', None)
        data['visible'] = bool(visible) if visible is not None else None
        data['place'] = str(request.GET.get('place', ''))
        data['title_or_author'] = str(request.GET.get('title_author', ''))
        types = request.GET.get('types', [])
        types = types.split(',') if isinstance(types, str) else types
        for type_ in types:
            if not any(type_ == t for t, _ in Event.TYPES):
                raise ValueError
        data['types'] = types
        statuses = request.GET.get('statuses', [])
        statuses = statuses.split(',') if isinstance(statuses, str) else statuses
        for status in statuses:
            if not any(status == s for s, _ in Event.STATUSES):
                raise ValueError
        data['statuses'] = statuses
        rooms = request.GET.get('rooms', [])
        data['rooms'] = rooms.split(',') if rooms else rooms
        return data
    except (ValueError, TypeError, KeyError):
        raise ValidationError('Przesłane dane są nieprawidłowe lub niewystarczające')


@login_required
def terms(request):
    """ Return list of Terms info needed for fullcalendar event fetching.

        Args:
            request - GET request sent from fullcalendar.
        Returns:
            JsonResponse with List of Dicts. Single Dict contains info about single term to display in fullcalendar.
            Single term here contains info from Event too: title, status, type etc.
    """
    try:
        data = _check_and_prepare_get_data(request)
    except ValidationError as err:
        return HttpResponseBadRequest(err)
    query = Term.objects.order_by().filter(day__range=[data['start'], data['end']]).select_related('event',
                                                                                                   'event__author')
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
    if data['visible'] is not None:
        query = query.filter(event__visible=data['visible'])
    query = query.distinct('event', 'day', 'start', 'end')
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
                        "user_is_author": request.user == event.author,
                        "start": datetime.combine(term.day, term.start).isoformat(),
                        "end": datetime.combine(term.day, term.end).isoformat()})
    return JsonResponse(payload, safe=False)


def _get_event_author_url(author, user):
    """ Return tuple (author, author_url).

        If student hid his name and logged user is not employee return tuple (None, None).

        Args:
            author: Event.author
            user: Logged request.user.
        Returns:
            Tuple(author: str, author_url: str) or Tuple(author: None, author_url: None).
    """
    if not author:
        return None, None
    if is_employee(author):
        author_url = reverse('employee-profile', args=[author.pk])
    else:
        author_url = reverse('student-profile', args=[author.pk])
        student = Student.objects.get(user=author)
        if not student.consent_granted() and not user.employee:
            author = None
            author_url = None
    return author, author_url


def _get_validated_terms(payload, event=None):
    """ From given payload return List of Terms.

        From payload get List of Terms - dictionaries. Payload term may have key 'rooms'. This function make
        separate Term object for every room number in 'rooms'. Term can have only room or place, not both.
        Runs clean() on every Term, but not save(). So it does not change database.

        Args:
            payload: Dict from POST request body (JSON).
            event: Create every Term with this event.
        Returns:
            List of Terms.
        Raises:
            ValidationError: When any Term info miss 'start', 'end' or 'day' key with proper datetime format string.
                             When any Term miss both 'rooms' and 'place' field.
                             When any room number in 'rooms' key is not found as proper Classroom object to reserve.
    """
    try:
        payload_terms = payload.get('terms', [])
        if not payload_terms:
            raise ValueError
        terms = []
        for payload_term in payload_terms:
            term = Term(event=event)
            term.start = datetime.strptime(payload_term['start'], '%H:%M').time()
            term.end = datetime.strptime(payload_term['end'], '%H:%M').time()
            term.day = datetime.strptime(payload_term['day'], '%Y-%m-%d').date()
            if 'rooms' in payload_term and payload_term['rooms']:
                for room_number in payload_term['rooms']:
                    room = Classroom.objects.get(number=room_number)
                    term.room = room
                    term.place = None
                    term.clean()
                    terms.append(term)
                    term = copy.deepcopy(term)
            else:
                term.room = None
                term.place = payload_term['place']
                term.clean()
                terms.append(term)
        if not terms:
            raise ValueError
        return terms
    except (ValueError, TypeError, KeyError, ObjectDoesNotExist):
        raise ValidationError('Przesłane dane są nieprawidłowe lub niewystarczające')


def _check_conflicts(new_terms, present_terms=[]):
    """ Check if new_terms make conflicts with other Terms in database except present_terms. Return conflicting Terms.

        Args:
            new_terms: Terms to check if conflicts exists.
            present_terms: Ignore conflicts with these Terms.
        Returns:
            List of Dict. Single Dict contains information about Term and Event that is colliding.
            Structure of this Dict is inside _send_conflicts function.
    """
    conflicts_terms = set()
    for new_term in new_terms:
        temp_conflicts = new_term.get_conflicted_except_given_terms(present_terms)
        for conflict in temp_conflicts:
            conflicts_terms.add(conflict)
    return conflicts_terms


def _send_conflicts(conflicts, status=200):
    """ Return JsonResponse with proper conflicts structure and status.

        Args:
            conflicts: list of Terms.
            status: status of JsonResponse.
        Returns:
            JsonResponse with List of proper conflicts dict for frontend. Set given status to response.
    """
    payload = []
    for term in conflicts:
        payload.append({"title": term.event.title,
                        "description": term.event.description,
                        "status": term.event.status,
                        "type": term.event.type,
                        "visible": term.event.visible,
                        "url": term.event.get_absolute_url(),
                        "start": term.start,
                        "end": term.end,
                        "day": term.day,
                        "room": term.room.number if term.room else None,
                        "place": term.place})
    return JsonResponse(payload, safe=False, status=status)


@login_required
@require_POST
def check_conflicts(request, event_id=None):
    """ Return JsonResponse with conflicts, if they don't exists send empty list.

        Args:
            request: POST request. Retrieve Terms from request to check their conflicts.
            event_id: Id of Event which Terms are checked for collisions. With that given, Terms from request are not
                      colliding with existing Event Terms.
        Returns:
            JsonResponse with List of conflicts Dict for frontend, this List may be empty. Set given status to response.
    """
    payload = json.loads(request.body)
    try:
        if event_id:
            event = Event.objects.get(id=event_id)
            conflicts = _check_conflicts(_get_validated_terms(payload),
                                         present_terms=event.term_set.all().select_related('room'))
        else:
            conflicts = _check_conflicts(_get_validated_terms(payload))
    except (ValidationError, ObjectDoesNotExist) as err:
        return HttpResponseBadRequest(err)
    return _send_conflicts(conflicts, status=200)


def _prepare_create_update_return_dict(event, user, terms):
    """ Return Dict with proper keys and values for frontend. Used after successfully creating or updating Event.

        Args:
            event: Created or updated Event.
            user: Logged request.user.
            terms: List of Terms.
    """
    author, author_ulr = _get_event_author_url(event.author, user)
    return {"terms": [{"start": t.start,
                       "end": t.end,
                       "day": t.day,
                       "room": t.room.number if t.room else None,
                       "place": t.place} for t in terms],
            "description": event.description,
            "author": author.get_full_name() if author else None,
            "author_url": author_ulr,
            "title": event.title,
            "status": event.status,
            "type": event.type,
            "visible": event.visible,
            "url": event.get_absolute_url()}


@transaction.atomic
def create_event(request):
    """ Create Event with request payload properties. Before creating, Event and Terms are validated.

        Args:
            request: POST request.
        Returns:
            JsonResponse with created Event data. When logged user is not authorized HttpResponseForbidden.
            When sent payload is not valid HttpResponseBadRequest.
    """
    payload = json.loads(request.body)
    event = Event()
    event.title = payload.get('title', '')
    event.author = request.user
    event.description = payload.get('description', '')
    event.visible = payload.get('visible', True)
    event.status = payload.get('status', Event.STATUS_PENDING)
    event.type = payload.get('type', Event.TYPE_GENERIC)
    try:
        event.clean()
        event.save()
        terms = _get_validated_terms(payload, event=event)
        conflicts = _check_conflicts(terms)
    except ValidationError as err:
        if err.code == 'permission':
            return HttpResponseForbidden(err)
        return HttpResponseBadRequest(err)
    if conflicts:
        return _send_conflicts(conflicts, status=400)
    for term in terms:
        term.save()
    return JsonResponse(_prepare_create_update_return_dict(event, request.user, terms), status=201)


@transaction.atomic
def update_event(request, event_id):
    """ Update Event with request payload properties. Before updating, Event and Terms are validated.

        Replaces all existing Terms with new created Terms from sent payload.

        Args:
            request: POST request.
            event_id: Updating Event id.
        Returns:
            JsonResponse with updated Event data. When ValidationError error occurs then HttpResponseForbidden or
            HttpResponseBadRequest with proper text message.
    """
    payload = json.loads(request.body)
    try:
        event = Event.get_event_or_404(event_id, request.user)
        event.title = payload.get('title', '')
        event.author = request.user
        event.description = payload.get('description', '')
        event.visible = payload.get('visible', True)
        event.status = payload.get('status', Event.STATUS_PENDING)
        event.type = payload.get('type', Event.TYPE_GENERIC)
        event.clean()
        event.save()
        new_terms = _get_validated_terms(payload, event=event)
        present_terms = event.term_set.all().select_related('room')
        conflicts = _check_conflicts(new_terms, present_terms=present_terms)
    except ValidationError as err:
        if err.code == 'permission':
            return HttpResponseForbidden(err)
        return HttpResponseBadRequest(err)
    if conflicts:
        return _send_conflicts(conflicts, status=400)
    for present_term in present_terms:
        present_term.delete()
    for new_term in new_terms:
        new_term.save()
    return JsonResponse(_prepare_create_update_return_dict(event, request.user, new_terms), status=201)


def _group_terms_same_room(terms):
    """ Group terms with same date, hours and room. Return List of Dict with proper Term info structure for frontend.

        Args:
            terms: List of Terms.
        Returns:
            List of Dict with Term info for frontend.
    """
    new_terms = []
    for term in terms:
        insert_to_new_terms = True
        for new_term in new_terms:
            if term.start == new_term["start"] and term.end == new_term["end"] and term.day == new_term["day"] \
                    and term.place is None and new_term["place"] is None:
                new_term["rooms"].append(term.room.number)
                insert_to_new_terms = False
                break
        if insert_to_new_terms:
            new_terms.append({"start": term.start,
                              "end": term.end,
                              "day": term.day,
                              "rooms": [term.room.number] if term.room else None,
                              "place": term.place})
    return new_terms


def _prepare_events_return_dict(event, user):
    """ Prepare all needed info from Event object for frontend. This is not used by fullcalendar.

        Used in 'event' and 'events' function after filtering and validating GET query parameters.

        Args:
            event: Event to retrieve info for.
            user: logged request.user.
        Returns:
            Event info Dict with proper keys for frontend.
    """
    terms = event.term_set.all().select_related('room')
    author, author_url = _get_event_author_url(event.author, user)
    return {"terms": _group_terms_same_room(terms),
            "description": event.description,
            "author": author.get_full_name() if author else None,
            "author_url": author_url,
            "user_is_author": user == author,
            "title": event.title,
            "status": event.status,
            "type": event.type,
            "visible": event.visible,
            "created": event.created,
            "edited": event.edited,
            "url": event.get_absolute_url()}


@login_required
def events(request):
    """ Retrieve many Events or create single Event. This is not used by fullcalendar.

        When request method is GET, get sent query parameters and filter Events.
        Send only these Events that can be seen by a user.
        When request method is POST, validate if user can create Event with sent JSON properties and create Event.

        Args:
            request: GET or POST request.
        Returns:
            JsonResponse with retrieved Events and Terms or created Event and Terms.
    """
    if request.method == "POST":
        return create_event(request)
    try:
        data = _check_and_prepare_get_data(request, require_dates=False)
    except ValidationError as err:
        return HttpResponseBadRequest(err)
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
    query = query.order_by('-created')
    query = Paginator(query, 20).get_page(data['page'])
    payload = []
    for event in query:
        if not event._user_can_see_or_404(request.user):
            continue
        payload.append(_prepare_events_return_dict(event, request.user))
    return JsonResponse(payload, safe=False)


@login_required
@require_POST
@transaction.atomic
def delete_event(request, event_id):
    """ Delete Event after authorizing user.

        Args:
            request: POST request.
            event_id: Event Id to delete.
        Returns:
            HttpResponse when event is deleted. When event is not found HttpResponseBadRequest. When user is not
            authorized to delete Event HttpResponseForbidden.
    """
    try:
        event = Event.get_event_or_404(event_id, request.user)
    except Http404:
        return HttpResponseBadRequest("Event matching query does not exist.")
    if not request.user.has_perm('schedule.manage_events') and event.author != request.user:
        return HttpResponseForbidden('Nie można usuwać wydarzeń nie będąc ich autorem')
    event.delete()
    return HttpResponse("Event deleted", status=200)


@login_required
def event(request, event_id):
    """ Retrieve single Event or create single Event. This is not used by fullcalendar.

        When request method is GET, send single Event info if logged user can see this event. When request method
        is POST, validate if user can update Event with sent JSON properties and update Event.

        Args:
            request: GET or POST request.
            event_id: Event ID to retrieve or update.
        Returns:
            JsonResponse with retrieved Event and Terms or updated Event and Terms.
    """
    try:
        if request.method == "POST":
            return update_event(request, event_id)
        event = Event.get_event_or_404(event_id, request.user)
    except Http404:
        return HttpResponseBadRequest("Event matching query does not exist.")
    return JsonResponse(_prepare_events_return_dict(event, request.user))


class TableReportForm(forms.Form):
    """Form for generating table-based events report."""
    today = date.today().isoformat()
    beg_date = forms.DateField(
        label='Od:',
        widget=forms.TextInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'value': today}))
    end_date = forms.DateField(
        label='Do:',
        widget=forms.TextInput(
            attrs={
                'type': 'date',
                'class': 'form-control',
                'value': today}))
    rooms = forms.MultipleChoiceField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        classrooms = Classroom.objects.filter(can_reserve=True)
        by_floor = defaultdict(list)
        floor_names = dict(Floors.choices)
        for r in classrooms:
            by_floor[floor_names[r.floor]].append((r.pk, r.number))
        self.fields['rooms'].choices = by_floor.items()


class DoorChartForm(forms.Form):
    """Form for generating door event charts."""
    today = date.today().isoformat()
    rooms = forms.MultipleChoiceField()
    week = forms.CharField(max_length=10, widget=forms.Select())

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        classrooms = Classroom.objects.filter(can_reserve=True)
        by_floor = defaultdict(list)
        floor_names = dict(Floors.choices)
        for r in classrooms:
            by_floor[floor_names[r.floor]].append((r.pk, r.number))
        self.fields['rooms'].choices = by_floor.items()

        semester = Semester.get_current_semester()
        next_sem = Semester.get_upcoming_semester()
        weeks = [(week[0], f"{week[0]} - {week[1]}") for week in semester.get_all_weeks()]
        if semester != next_sem:
            weeks.insert(0, ('nextsem', f"Generuj z planu zajęć dla semestru '{next_sem}'"))
        weeks.insert(0, ('currsem', f"Generuj z planu zajęć dla semestru '{semester}'"))
        self.fields['week'].widget.choices = weeks


@login_required
@permission_required('schedule.manage_events')
def events_report(request):
    form_table = None
    form_doors = None
    if request.method == 'POST':
        # Pick the form that was sent.
        if request.POST['report-type'] == 'table':
            form = form_table = TableReportForm(request.POST)
            report_type = 'table'
        else:
            form = form_doors = DoorChartForm(request.POST)
            report_type = 'doors'
        if form.is_valid():
            return display_report(request, form, report_type)
    else:
        # Just display two forms.
        form_table = TableReportForm()
        form_doors = DoorChartForm()
    return render(request, 'schedule/reports/forms.html', {
        'form_table': form_table,
        'form_doors': form_doors,
    })


@login_required
@permission_required('schedule.manage_events')
def display_report(request, form, report_type: 'Literal["table", "doors"]'):  # noqa: F821
    class ListEvent(NamedTuple):
        date: Optional[datetime]
        weekday: int  # Monday is 1, Sunday is 7 like in
        # https://docs.python.org/3/library/datetime.html#datetime.date.isoweekday.
        begin: datetime.time
        end: datetime.time
        room: Classroom
        title: str
        type: str
        author: str

    rooms = set(Classroom.objects.filter(id__in=form.cleaned_data['rooms']))
    events: List[ListEvent] = []
    # Every event will regardless of its origin be translated into a ListEvent.
    beg_date = form.cleaned_data.get('beg_date', None)
    end_date = form.cleaned_data.get('end_date', None)
    semester = None
    if form.cleaned_data.get('week', None) == 'currsem':
        semester = Semester.get_current_semester()
    elif form.cleaned_data.get('week', None) == 'nextsem':
        semester = Semester.get_upcoming_semester()
    if semester:
        terms = CourseTerm.objects.filter(
            group__course__semester=semester, classrooms__in=rooms).distinct().select_related(
            'group__course', 'group__teacher',
            'group__teacher__user').prefetch_related('classrooms')
        for term in terms:
            for r in set(term.classrooms.all()) & rooms:
                events.append(
                    ListEvent(date=None,
                              weekday=int(term.dayOfWeek),
                              begin=term.start_time,
                              end=term.end_time,
                              room=r,
                              title=term.group.course.name,
                              type=term.group.get_type_display(),
                              author=term.group.teacher.get_full_name()))
        special_reservation_events = Event.objects.filter(type=Event.TYPE_SPECIAL_RESERVATION)
        semester_start_day = semester.semester_beginning
        semester_end_day = semester.semester_ending
        terms = []
        # Special reservations have same room, start and end every week. Do not duplicate those terms
        for event in special_reservation_events:
            same_room_hour_terms = set()
            temp_terms = event.term_set.all()
            for term in temp_terms:
                if semester_start_day <= term.day <= semester_end_day and term.room in rooms \
                        and (term.room, term.start, term.end) not in same_room_hour_terms:
                    same_room_hour_terms.add((term.room, term.start, term.end))
                    terms.append(term)
        for term in terms:
            events.append(
                ListEvent(date=None,
                          weekday=term.day.isoweekday(),
                          begin=term.start,
                          end=term.end,
                          room=term.room,
                          title=term.event.title,
                          type="",
                          author=""))
    elif 'week' in form.cleaned_data:
        beg_date = datetime.strptime(form.cleaned_data['week'], "%Y-%m-%d")
        end_date = beg_date + timedelta(days=6)
    if beg_date and end_date:
        terms = Term.objects.filter(day__gte=beg_date,
                                    day__lte=end_date,
                                    room__in=rooms,
                                    event__status=Event.STATUS_ACCEPTED).select_related(
            'room', 'event', 'event__group', 'event__author')
        for term in terms:
            events.append(
                ListEvent(date=term.day,
                          weekday=term.day.isoweekday(),
                          begin=term.start,
                          end=term.end,
                          room=term.room,
                          title=term.event.title or str(term.event.course) or "",
                          type=term.event.group.get_type_display()
                          if term.event.group else term.event.get_type_display(),
                          author=term.event.author.get_full_name()))
    if report_type == 'table':
        events = sorted(events, key=operator.attrgetter('room.id', 'date', 'begin'))
    else:
        events = sorted(events, key=operator.attrgetter('room.id', 'weekday', 'begin'))
    terms_by_room = groupby(events, operator.attrgetter('room.number'))
    terms_by_room = sorted([(int(k), list(g)) for k, g in terms_by_room])

    return render(request, f'schedule/reports/report_{report_type}.html', {
        'events': terms_by_room,
        'semester': semester,
        'beg_date': beg_date,
        'end_date': end_date,
    })
