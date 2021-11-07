from django import forms
from .models import Defect, DEFECT_MAX_PLACE_SIZE, DEFECT_MAX_NAME_SIZE
from apps.common import widgets as common_widgets


class DefectFormBase(forms.ModelForm):
    class Meta:
        model = Defect
        exclude = ["reporter", 'creation_date', 'last_modification']

    name = forms.CharField(label="Nazwa", max_length=DEFECT_MAX_NAME_SIZE)
    place = forms.CharField(label="Miejsce usterki", max_length=DEFECT_MAX_PLACE_SIZE)
    description = forms.CharField(
        label="Opis", widget=common_widgets.MarkdownArea, required=False)

    def __init__(self, user, *args, **kwargs):
        super(DefectFormBase, self).__init__(*args, **kwargs)
        self.reporter = user


class DefectForm(DefectFormBase):
    def __init__(self, user, *args, **kwargs):
        super(DefectForm, self).__init__(user, *args, **kwargs)
