from django.db import models

# Create your models here.


class File(models.Model):
    name = models.CharField(max_length=255)
    file_path = models.CharField(max_length=255)

