from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.theses.enums import ThesisStatus, ThesisVote
from apps.theses.forms import EditThesisForm, RejecterForm, RemarkForm, ThesisForm, VoteForm
from apps.theses.models import Thesis
from apps.theses.users import get_theses_board, is_master_rejecter, is_theses_board_member
from apps.users.decorators import employee_required
from apps.users.models import Student


@login_required
def list_all(request):
    """Display list of all visible theses."""
    visible_theses = Thesis.objects.visible(request.user).select_related(
        'advisor', 'advisor__user').prefetch_related('students', 'students__user')
    board_member = is_theses_board_member(request.user)

    theses_list = []
    for p in visible_theses:
        title = p.title
        is_available = not p.is_reserved
        kind = p.get_kind_display()
        status = p.get_status_display()
        is_mine = p.is_mine(request.user) or p.is_student_assigned(
            request.user) or p.is_supporting_advisor_assigned(request.user)
        advisor = str(p.advisor) + (f" ({p.supporting_advisor})" if p.supporting_advisor else "")
        advisor_last_name = p.advisor.user.last_name if p.advisor else p.advisor.__str__()
        students = ", ".join(s.get_full_name() for s in p.students.all())
        url = reverse('theses:selected_thesis', None, [str(p.id)])

        record = {
            'id': p.id,
            'title': title,
            'is_available': is_available,
            'reserved_until': p.reserved_until,
            'kind': kind,
            'status': status,
            'is_mine': is_mine,
            'url': url,
            'advisor': advisor,
            'advisor_last_name': advisor_last_name,
            'students': students,
            'modified': p.modified.timestamp()
        }

        theses_list.append(record)

    return render(request, 'theses/list_all.html', {
        'theses_list': theses_list,
        'board_member': board_member,
    })


@login_required
def view_thesis(request, id):
    """Show subpage for one thesis."""
    thesis = get_object_or_404(Thesis, id=id)
    board_member = is_theses_board_member(request.user)

    user_privileged_for_thesis = thesis.is_among_advisors(
        request.user) or request.user.is_staff or board_member

    if not thesis.has_been_accepted and not user_privileged_for_thesis:
        raise PermissionDenied
    can_edit_thesis = (request.user.is_staff or thesis.is_mine(request.user))
    save_and_verify = thesis.is_mine(request.user) and thesis.is_returned
    can_vote = thesis.is_voting_active and board_member
    show_master_rejecter = is_master_rejecter(request.user) and (
        thesis.is_voting_active or thesis.is_returned)
    can_download_declarations = thesis.is_student_assigned(
        request.user) or user_privileged_for_thesis

    students = thesis.students.all()

    all_voters = get_theses_board()
    votes = []
    voters = []
    for vote in thesis.thesis_votes.all():
        voters.append(vote.owner)
        votes.append({'owner': vote.owner,
                      'vote': vote.get_vote_display()})

    for voter in all_voters:
        if voter not in voters:
            votes.append({'owner': voter,
                          'vote': ThesisVote.NONE.label})

    for vote in votes:
        if vote['owner'].user == request.user:
            votes.remove(vote)
            votes.insert(0, vote)

    vote_form_accepted = VoteForm(vote=ThesisVote.ACCEPTED)
    vote_form_rejected = VoteForm(vote=ThesisVote.REJECTED)
    vote_form_none = VoteForm(vote=ThesisVote.NONE)

    rejecter_accepted = RejecterForm(status=ThesisStatus.ACCEPTED)
    if thesis.is_voting_active:
        rejecter_rejected = RejecterForm(
            status=ThesisStatus.RETURNED_FOR_CORRECTIONS)
    else:
        rejecter_rejected = RejecterForm(
            status=ThesisStatus.BEING_EVALUATED
        )

    remarks = None
    remarkform = None

    if board_member and not thesis.has_been_accepted:
        remarks = thesis.thesis_remarks.all().exclude(
            author=request.user.employee).exclude(text="")
        remarkform = RemarkForm(thesis=thesis, user=request.user)
    elif user_privileged_for_thesis:
        remarks = thesis.thesis_remarks.all().exclude(text="")

    remarks_exist = not thesis.has_been_accepted or remarks

    max_number_of_students = thesis.max_number_of_students

    return render(
        request, 'theses/thesis.html', {
            'thesis': thesis,
            'students': students,
            'board_member': board_member,
            'show_master_rejecter': show_master_rejecter,
            'can_see_remarks': user_privileged_for_thesis,
            'save_and_verify': save_and_verify,
            'can_vote': can_vote,
            'can_edit_thesis': can_edit_thesis,
            'can_download_declarations': can_download_declarations,
            'remarks': remarks,
            'remark_form': remarkform,
            'remarks_exist': remarks_exist,
            'votes': votes,
            'vote_form_accepted': vote_form_accepted,
            'vote_form_rejected': vote_form_rejected,
            'vote_form_none': vote_form_none,
            'rejecter_accepted': rejecter_accepted,
            'rejecter_rejected': rejecter_rejected,
            'max_number_of_students': max_number_of_students,
        })


@login_required
def gen_form(request, id, studentid):
    """Display form to print for specific student assigned to a thesis."""
    thesis = get_object_or_404(Thesis, id=id)
    try:
        first_student = thesis.students.get(id=studentid)
    except Student.DoesNotExist:
        raise Http404("No Student matches the given query.")

    user_privileged_for_thesis = thesis.is_among_advisors(
        request.user) or request.user.is_staff or is_theses_board_member(request.user)
    user_allowed_to_generate = user_privileged_for_thesis or (
        thesis.has_been_accepted and thesis.is_student_assigned(request.user))
    if not user_allowed_to_generate:
        raise PermissionDenied

    students = []
    for student in thesis.students.all():
        if(student.id != studentid):
            students.append(student)

    students_num = len(students) + 1

    return render(
        request, 'theses/form_pdf.html', {
            'thesis': thesis,
            'first_student': first_student,
            'students': students,
            'students_num': students_num
        })


@employee_required
def edit_thesis(request, id):
    """Show form for edit selected thesis."""
    thesis = get_object_or_404(Thesis, id=id)
    if not request.user.is_staff and not thesis.is_mine(request.user):
        raise PermissionDenied
    if request.method == "POST":
        form = EditThesisForm(request.user, request.POST, instance=thesis)
        # check whether it's valid:
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, 'Zapisano zmiany')
            return redirect('theses:selected_thesis', id=id)
    else:
        form = EditThesisForm(request.user, instance=thesis)

    return render(request, 'theses/thesis_form.html', {
        'thesis_form': form,
        'title': thesis.title,
        'id': id
    })


@employee_required
def new_thesis(request):
    """Show form for create new thesis."""
    if request.method == "POST":
        form = ThesisForm(request.user, request.POST)
        # check whether it's valid:
        if form.is_valid():
            form.save(commit=True)
            messages.success(request, 'Dodano nową pracę')
            return redirect('theses:main')
    else:
        form = ThesisForm(request.user)
    return render(request, 'theses/thesis_form.html', {'thesis_form': form, 'new_thesis': True})


@employee_required
def edit_remark(request, id):
    """Edit remark for selected thesis."""
    if not is_theses_board_member(request.user):
        raise PermissionDenied
    thesis = get_object_or_404(Thesis, id=id)
    if thesis.has_been_accepted:
        raise PermissionDenied
    if request.method == "POST":
        form = RemarkForm(request.POST, thesis=thesis, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, 'Zapisano uwagę')
    return redirect('theses:selected_thesis', id=id)


@employee_required
def vote_for_thesis(request, id):
    """Vote for selected thesis."""
    if not is_theses_board_member(request.user):
        raise PermissionDenied
    thesis = get_object_or_404(Thesis, id=id)
    if thesis.has_been_accepted:
        raise PermissionDenied
    if request.method == "POST":
        form = VoteForm(request.POST, thesis=thesis, user=request.user)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, 'Zapisano głos')
    return redirect('theses:selected_thesis', id=id)


@employee_required
def rejecter_decision(request, id):
    """Change status of selected thesis."""
    if not is_master_rejecter(request.user):
        raise PermissionDenied
    thesis = get_object_or_404(Thesis, id=id)
    if thesis.has_been_accepted:
        raise PermissionDenied
    if request.method == "POST":
        form = RejecterForm(request.POST, instance=thesis)
        if form.is_valid():
            post = form.save(commit=False)
            post.save()
            messages.success(request, 'Zapisano decyzję')
    return redirect('theses:selected_thesis', id=id)


@require_POST
@employee_required
def delete_thesis(request, id):
    """Delete selected thesis."""
    thesis = get_object_or_404(Thesis, id=id)
    if not request.user.is_staff and not thesis.is_mine(request.user):
        raise PermissionDenied
    thesis.delete()
    messages.success(request, 'Pomyślnie usunięto pracę dyplomową')
    return redirect('theses:main')
