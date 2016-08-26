# -*- coding: utf-8 -*-
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import login as auth_login
from django.contrib.auth.views import logout as auth_logout
from django.core.urlresolvers import reverse
from django.forms import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render_to_response
from django.template.context_processors import csrf

import logging
logger = logging.getLogger(__name__)

DEFAULT_REDIRECT = 'logic:index'

def _get_default_redirect():
    return reverse(DEFAULT_REDIRECT)

def _user_exists(name):
    return len(User.objects.filter(username=name)) > 0

def _is_valid(name):
    return len(name) == 9 and all(c.isdigit() for c in name)

def login(request):
    context = {}
    if request.method == 'GET':
        if request.user.is_authenticated():
            logger.info('already logged in: %s', request.user)
            return HttpResponseRedirect(_get_default_redirect())
        context['title'] = 'לוגיקה'
        context['next'] = _get_default_redirect()
    else: # POST
        username = request.POST['username']
        logger.info('login post: username=%s', username)
        context['username'] = username
        context['password'] = request.POST['password']
        if not _user_exists(username) and _is_valid(username):
            logger.info('login first time: %s', username)
            context['first_time'] = True
            context['groups'] = ['%02d' % i for i in range(2,9+1)] # TODO: put this in settings

    return auth_login(
        request,
        redirect_field_name = 'next',
        authentication_form = UserAuthForm,
        extra_context = context
    )

def logout(request):
    logger.info('logout: %s', request.user)
    return auth_logout(request, next_page=_get_default_redirect())

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        logger.info('registering new user, data: %s', request.POST)
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
        return HttpResponseRedirect(_get_default_redirect())

class UserAuthForm(AuthenticationForm):

    def __init__(self, *args, **kwargs):
        super(UserAuthForm, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        username = self.cleaned_data.get('username')
        if not _user_exists(username):
            if not _is_valid(username):
                raise ValidationError('יש להזין מספר ת.ז. תקין בן תשע ספרות') 
            else:
                # to prompt new user creation without error messages
                raise ValidationError('')
        super(UserAuthForm, self).clean(*args, **kwargs)
