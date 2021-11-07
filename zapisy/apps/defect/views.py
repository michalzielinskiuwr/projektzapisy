from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import DefectForm
from ..users.decorators import employee_required


def index(_request):
    return HttpResponse("Hello, world. You're at the polls index.")  # TODO REMOVE


# @employee_required
def add_defect(request):
    """Show form for create new defect."""

    if request.method == 'POST':
        form = DefectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('defect')

    else:
        form = DefectForm(user=request.user)
        context = {'form': form, }

    return render(request, 'addDefect.html', context)
