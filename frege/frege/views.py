# -*- coding: utf-8 -*-
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import login as auth_login
from django.contrib.auth.views import logout as auth_logout
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render_to_response
from django.template.context_processors import csrf

DEFAULT_REDIRECT = 'logic:index'

def _get_default_redirect():
    return reverse(DEFAULT_REDIRECT)

def login(request):
    context = {}
    if request.method == 'GET':
        if request.user.is_authenticated():
            return HttpResponseRedirect(_get_default_redirect())
        context['title'] = 'לוגיקה'
        context['next'] = _get_default_redirect()
    return auth_login(
        request,
        redirect_field_name = 'next',
        authentication_form = UserAuthForm,
        extra_context = context
    )

def logout(request):
    return auth_logout(request, next_page=_get_default_redirect())

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # save the new user
            form.save()
            # autologin and redirect home
            post = request.POST.copy()
            post['password'] = request.POST['password1']
            post['next'] = _get_default_redirect()
            request.POST = post
            return auth_login(request, redirect_field_name='next')
    else:
        form = UserCreationForm()

    context = {}
    context.update(csrf(request))
    context['form'] = form
    context['site_header'] = 'רישום משתמש חדש'
    context['site_title'] = 'רישום'
    context['title'] = 'לוגיקה'

    return render_to_response('registration/register.html', context)

class UserAuthForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(UserAuthForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        if not User.objects.filter(username=self.cleaned_data.get('username')):
            raise ValidationError('שם לא קיים')
        super(UserAuthForm, self).clean(*args, **kwargs)
