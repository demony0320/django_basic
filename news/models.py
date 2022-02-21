from django.db import models

class Article(models.Model):
    subject_text = models.CharField(max_length=200)
    contents_text = models.CharField(max_length=3000)
    update_date = models.DateTimeField('updated date')
    writer_text = models.CharField(max_length=50)

