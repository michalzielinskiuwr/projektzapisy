import json

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.timezone import now

from .forms import DefectForm
from .models import Defect, StateChoices
from ..users.decorators import employee_required


@employee_required
def index(request):
    if request.method == "POST":
        query = request.POST
        defects_list = parse_names(request)
        if defects_list is None or len(defects_list) == 0 and query.get('print') is None:
            messages.error(request, "Akcja wymaga zaznaczenia elementów")
        elif query.get('print') is not None:
            if defects_list is None or len(defects_list) == 0:
                return print_defects(request)
            return print_defects(request, Defect.objects.filter(pk__in=defects_list))
        elif query.get('done') is not None:
            Defect.objects.filter(pk__in=defects_list).update(state=StateChoices.DONE)
        elif query.get('delete') is not None:
            to_delete = Defect.objects.filter(pk__in=defects_list)
            query_set = ", ".join(map(lambda x: x['name'], list(to_delete.values())))
            messages.info(request, "Usunięto następujące usterki: " + query_set)
            to_delete.delete()
        else:
            messages.error(request, "Nie wprowadzono metody. Ten błąd nie powinien się zdarzyć. Proszę o kontakt z "
                           "administratorem systemu zapisów.")
    return render(request, 'defectMain.html', {'defects': Defect.objects.all()})


def parse_names(request):
    try:
        return list(map(int, request.POST.getlist("names[]")))
    except Exception:
        return None


@employee_required
def add_defect(request):
    """Show form for create new defect."""
    if request.method == 'POST':
        return handle_post_request(request)
    else:
        form = DefectForm()
    context = {'form': form, "response": request.method}
    return render(request, 'addDefect.html', context)


@employee_required
def show_defect(request, defect_id):
    try:
        defect = Defect.objects.get(pk=defect_id)
        return render(request, 'showDefect.html', {'defect': defect})
    except Defect.DoesNotExist:
        messages.error(request, "Nie istnieje usterka o podanym id.")
        return redirect('defects:main')


@employee_required
def edit_defect(request, defect_id):
    try:
        defect = Defect.objects.get(pk=defect_id)
        return edit_defect_helper(request, defect)
    except Defect.DoesNotExist:
        messages.error(request, "Nie istnieje usterka o podanym id.")
        return redirect('defects:main')


def edit_defect_helper(request, defect):
    if request.method == 'POST':
        return handle_post_request(request, if_edit=True, defect_id=defect.id)
    else:
        form = DefectForm(instance=defect)
    context = {'form': form, "response": request.method, "edit": True}
    return render(request, 'addDefect.html', context)


def handle_post_request(request, if_edit=False, defect_id=None):
    form = DefectForm(request.POST)
    if form.is_valid():
        creation_date = now()
        form_data = form.cleaned_data
        if if_edit:
            Defect.objects.filter(pk=defect_id).update(name=form_data['name'], last_modification=creation_date,
                            description=form_data['description'], state=form_data['state'], place=form_data['place'])
            messages.success(request, "Edytowano usterkę")
        else:
            defect = Defect(name=form_data['name'], creation_date=creation_date, last_modification=creation_date,
                            place=form_data['place'], description=form_data['description'], reporter=request.user,
                            state=form_data['state'])
            defect.save()
            messages.success(request, "Dodano usterkę")
        return redirect('defects:main')
    else:
        messages.error(request, str(form.errors))
        context = {'form': form, "response": request.method, "edit":if_edit}
        return render(request, 'addDefect.html', context)


def print_defects(request, defects_list=None):
    if defects_list==None:
        return render(request, 'defectPrint.html', {'defects' : Defect.objects.all()})
    else:
        return render(request, 'defectPrint.html', {'defects' : Defect.objects.filter(pk__in=defects_list)})
