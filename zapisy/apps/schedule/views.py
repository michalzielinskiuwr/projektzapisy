from django.template.response import TemplateResponse


def calendar(request):
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
