from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

DEFECT_MAX_NAME_SIZE = 255
DEFECT_MAX_PLACE_SIZE = 255


class StateChoices(models.IntegerChoices):
    CREATED = 0, "Stworzone"
    IMPOSSIBLE = 1, "Nie da się"
    LONGER_ISSUE = 2, "Dłuższy problem"
    DONE = 3, "Zrobione"


class Defect(models.Model):
    name = models.CharField(max_length=DEFECT_MAX_NAME_SIZE, verbose_name='Nazwa')
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modification = models.DateTimeField(auto_now_add=True)
    place = models.CharField(max_length=DEFECT_MAX_PLACE_SIZE, verbose_name="Miejsce")
    description = models.TextField("Opis usterki", blank=True)
    reporter = models.ForeignKey(User, on_delete=models.CASCADE)
    state = models.PositiveSmallIntegerField("Stan", choices=StateChoices.choices, default=StateChoices.CREATED)

    def get_url(self):
        return reverse('defects:show_defect', args=[str(self.id)])
