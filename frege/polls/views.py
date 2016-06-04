from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader

from .models import Question

def index(request):
    qlist = Question.objects.order_by('date')[:10]
    template = loader.get_template('polls/index.html')
    context = {
        'qlist' : qlist,
    }
    return render(request, 'polls/index.html', context)

def detail(request, qid):
    return HttpResponse("You're looking at the results of question %s." % qid) 

def vote(request, qid):
    return HttpResponse("You're voting on question %s." % qid) 
