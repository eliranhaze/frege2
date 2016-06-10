# -*- coding: utf-8 -*-
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.views import login as auth_login
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response

def login(request):
    context = {}
    if request.method == 'GET':
        context['site_header'] = 'התחברות'
        context['site_title'] = 'התחברות'
        context['title'] = 'לוגיקה'
    return auth_login(request, extra_context=context)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # save the new user
            form.save()
            # autologin and redirect home
            post = request.POST.copy()
            post['password'] = request.POST['password1']
            post['next'] = reverse('polls:index')
            request.POST = post
            return auth_login(request)
    else:
        form = UserCreationForm()

    context = {}
    context.update(csrf(request))
    context['form'] = form
    context['site_header'] = 'רישום משתמש חדש'
    context['site_title'] = 'רישום'
    context['title'] = 'לוגיקה'

    return render_to_response('registration/register.html', context)

