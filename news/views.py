from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import render
from .models import Article
from .forms import NewsForm


def index(request):
    latest_article_list= Article.objects.order_by('-date')[:5]
    #template = loader.get_template('news/index.html')
    context = { 'latest_article_list' : latest_article_list }
    return render(request, 'news/index.html', context)

def detail(request,article_id):
    try:
        article = Article.objects.get(pk=article_id)
    except Article.DoesNotExist:
        raise Http404(f"Article (id : {article_id}) does not exists")
    return render(request, 'news/detail.html', { 'article' : article } )
        
    

def post(request):
# if this is a POST request we need to process the form data
    if request.method == 'POST':
    # create a form instance and populate it with data from the request:
        form = NewsForm(request.POST)
        # check whether it's valid:
        if form.is_valid():
            # process the data in form.cleaned_data as required
            # ...
            # redirect to a new URL:
            form.save()
            return HttpResponseRedirect('/news/')
    else:
        form = NewsForm() # Blank form

    return render(request, 'news/post.html', {'form': form})
