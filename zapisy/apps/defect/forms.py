from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from django import forms
from django.forms import inlineformset_factory

from .models import Defect, DEFECT_MAX_PLACE_SIZE, DEFECT_MAX_NAME_SIZE, Image

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout, Row, Column, HTML, Div


class DefectFormBase(forms.ModelForm):
    class Meta:
        model = Defect
        fields = ["name", "place", "description", "state"]

    name = forms.CharField(label="Nazwa", max_length=DEFECT_MAX_NAME_SIZE)
    place = forms.CharField(label="Miejsce usterki", max_length=DEFECT_MAX_PLACE_SIZE)

    def __init__(self, *args, **kwargs):
        super(DefectFormBase, self).__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False


class DefectForm(DefectFormBase):
    def __init__(self, *args, **kwargs):
        super(DefectForm, self).__init__(*args, **kwargs)


class ImageForm(forms.ModelForm):

    class Meta:
        model = Image
        fields = ('image',)

    def __init__(self, *args, **kwargs):
        super(ImageForm, self).__init__(*args, **kwargs)
        self.fields['image'].required = False

        self.helper = FormHelper()
        self.helper.form_tag = False

        self.helper.layout = Layout(
            Div(
                'image',
                Div('DELETE', css_class='d-none'),
                css_class="image-form d-none"))


ExtraImagesNumber = 10
DefectImageFormSet = inlineformset_factory(Defect,
                                           Image,
                                           form=ImageForm,
                                           extra=ExtraImagesNumber,
                                           can_delete=True)

