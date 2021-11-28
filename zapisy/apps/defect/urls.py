from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='main'),
    path('new', views.add_defect, name='new'),
    path('defect/<int:id>', views.show_defect, name='show_defect'),
]
