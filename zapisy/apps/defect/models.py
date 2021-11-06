from django.db import models
from django.contrib.auth.models import User


class StateChoices(models.IntegerChoices):
    CREATED = 0, "Stworzone"
    IMPOSSIBLE = 1, "Nie da się"
    LONGER_ISSUE = 2, "Dłuższy problem"
    DONE = 3, "Zrobione"


class Defect(models.Model):
    title = models.CharField(max_length=255, verbose_name='Tytuł')
    date = models.DateTimeField(auto_now_add=True)
    place = models.CharField(max_length=255, verbose_name="Miejsce")
    description = models.TextField("Opis usterki", blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.PositiveSmallIntegerField("Stan", choices=StateChoices.choices, default=StateChoices.CREATED)
