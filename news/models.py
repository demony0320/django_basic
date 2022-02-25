from django.db import models

from django.forms import ModelForm

class Article(models.Model):
    subject= models.CharField(max_length=200)
    content= models.CharField(max_length=3000)
    date= models.DateTimeField('updated date')
    writer= models.CharField(max_length=50)
    def __str__(self):
        return f"{subject} by {writer} on {date}"

class ArticlForm(ModelForm):
    class Meta:
        model = Article
        fields=['subject','content','writer']
