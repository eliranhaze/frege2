from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render

from .models import Question

def index(request):
    qlist = Question.objects.order_by('date')[:10]
    return render(request, 'polls/index.html', {'qlist':qlist})

def detail(request, qid):
    q = get_object_or_404(Question, id=qid)
    return render(request, 'polls/detail.html', {'q':q})

def vote(request, qid):
    return HttpResponse("You're voting on question %s." % qid) 
