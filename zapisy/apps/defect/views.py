import logging

from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.timezone import now

from .forms import DefectForm
from .models import Defect


def index(request):
    return render(request, 'defectMain.html', {})  # TODO make this to be the list


# @employee_required
def add_defect(request):
    """Show form for create new defect."""
    logger = logging.getLogger(__name__)
    logger.info(request.method)
    logger.info(request.__dict__)
    if request.method == 'POST':
        form = DefectForm(request.POST)
        if form.is_valid():
            creation_date = now()
            form_data = form.cleaned_data
            defect = Defect(name=form_data['name'], creation_date=creation_date, last_modification=creation_date,
                            place=form_data['place'], description=form_data['description'], reporter=request.user,
                            state=form_data['state'])
            defect.save()
            messages.success(request, "Dodano pomyślnie usterkę")
            return redirect('defects:main')
        else:
            messages.error(request, str(form.errors))
            logger.error(form.non_field_errors())
            logger.error(str(form.errors))

    else:
        form = DefectForm()
    context = {'form': form, "response": request.method}
    return render(request, 'addDefect.html', context)
