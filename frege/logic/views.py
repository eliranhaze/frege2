from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

#from .models import Choice, Question

class IndexView(LoginRequiredMixin, generic.View):
    #template_name = 'logic/index.html'
    #context_object_name = 'qlist'

#    def get_queryset(self):
#        print 'User is %s' % self.request.user
#        return get_past_questions().order_by('-date')[:10]

    def get(self, request):
        return HttpResponse('Hello there!')

