from django import forms
from .models import Article

#from ckeditor.fields import RichTextFormField
#from ckeditor_uploader.fields import RichTextUploadingFormField

#class NewsForm(forms.Form):
#    your_name = forms.CharField(label='Your name', max_length=100)

class NewsForm(forms.ModelForm):
    class Meta:
        model = Article
        fields=['subject','content','writer']
