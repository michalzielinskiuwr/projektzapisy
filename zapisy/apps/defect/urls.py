from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='main'),
    path('new', views.add_defect, name='new'),
    path('<int:defect_id>', views.show_defect, name='show_defect'),
    path('<int:defect_id>/edit', views.edit_defect, name='edit_defect')
    path('image', views.add_image, name='image'),
    # path('create', DefectImageCreate.as_view(template_name="createDefectWithImages.html"), name='create'),
]
