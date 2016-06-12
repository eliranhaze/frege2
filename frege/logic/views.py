from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views import generic

from .models import Chapter

class IndexView(LoginRequiredMixin, generic.ListView):
    template_name = 'logic/index.html'

    def get_queryset(self):
        return Chapter.objects.all()

