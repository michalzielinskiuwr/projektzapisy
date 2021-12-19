import json

from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.views.generic import CreateView

from .models import Defect, StateChoices

from .forms import DefectForm, ImageForm, Image, DefectImageFormSet, ExtraImagesNumber


from ..users.decorators import employee_required

from gdstorage.storage import GoogleDriveStorage

# Define Google Drive Storage
gd_storage = GoogleDriveStorage()


@employee_required
def index(request):
    if request.method == "POST":
        query = request.POST
        defects_list = parse_names(request)
        if defects_list is None or len(defects_list) == 0:
            messages.error(request, "Akcja wymaga zaznaczenia elementów")
        elif query.get('print') is not None:
            messages.info(request, "Metoda nie zaimplementowana.")
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


def new_defect(request):
    if request.method == "POST":
        form = DefectForm(request.POST, request.FILES)
        formset = DefectImageFormSet(request.POST, request.FILES)
        if form.is_valid():
            defect = form.save(commit=False)
            formset = DefectImageFormSet(request.POST, request.FILES, instance=defect)

            if formset.is_valid():
                defect.save()
                formset.save()

                return redirect(defect)
    else:
        form = DefectForm()
        formset = DefectImageFormSet()
    return render(request,
                  'createDefectWithImages.html',
                  {'form': form, 'formset': formset, 'extra_images_number': ExtraImagesNumber})


def add_image(request):
    if request.method == "POST":
        image_form = ImageForm(request.POST, request.FILES)
        if image_form.is_valid():
            image_form.save()
        return redirect('defects:image')

    image_form = ImageForm()
    photos = Image.objects.all()
    return render(request=request, template_name="addImage.html",
                  context={'form': image_form, 'photos': photos})


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


