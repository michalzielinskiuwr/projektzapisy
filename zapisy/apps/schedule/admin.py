from django import forms
from django.contrib import admin

from .models.term import Term


class TermAdmin(admin.ModelAdmin):
    list_display = ('event', 'day', 'start', 'end', 'room', 'place')
    list_filter = ('room',)
    search_fields = ('event__title',)
    ordering = ('-day', 'start', 'end')


admin.site.register(Term, TermAdmin)