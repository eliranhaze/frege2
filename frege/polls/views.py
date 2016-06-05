from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.views import generic

from .models import Choice, Question

# Generic views

class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'qlist'

    def get_queryset(self):
        return Question.objects.order_by('-date')[:10]

class DetailView(generic.DetailView):
    model = Question
    template_name = 'polls/detail.html'
    context_object_name = 'q'

class ResultsView(generic.DetailView):
    model = Question
    template_name = 'polls/results.html'
    context_object_name = 'q'

# Explicit views

def index(request):
    qlist = Question.objects.order_by('date')[:10]
    return render(request, 'polls/index.html', {'qlist':qlist})

def detail(request, qid):
    q = get_object_or_404(Question, id=qid)
    return render(request, 'polls/detail.html', {'q':q})

def results(request, qid):
    q = get_object_or_404(Question, id=qid)
    return render(request, 'polls/results.html', {'q':q})

def vote(request, qid):
    q = get_object_or_404(Question, id=qid)
    try:
        # we make sure this is a post call by explicitly using request.POST
        sel = q.choice_set.get(id=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # back to form
        return render(request, 'polls/detail.html', {'q':q, 'error_message':'No choice selected.'})

    sel.votes += 1
    sel.save()
    # always return like this when dealing with post
    return HttpResponseRedirect(reverse('polls:results', args=(q.id,)))
