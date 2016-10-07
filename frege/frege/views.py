# -*- coding: utf-8 -*-
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.contrib.auth.views import login as auth_login
from django.contrib.auth.views import logout as auth_logout
from django.core.urlresolvers import reverse
from django.db import transaction
from django.forms import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render_to_response
from django.template.context_processors import csrf

from logic.models import UserProfile
from . import auth_ldap

import logging
logger = logging.getLogger(__name__)

DEFAULT_REDIRECT = 'logic:index'

def _get_default_redirect():
    return reverse(DEFAULT_REDIRECT)

def _user_exists(name):
    return User.objects.filter(username=name).count() > 0

def _is_valid(name):
     return True
#    return name and len(name) == 9 and all(c.isdigit() for c in name) # check for valid id number

def login(request):
    context = {}
    if request.method == 'GET':
        if request.user.is_authenticated():
            logger.info('already logged in: %s', request.user)
            return HttpResponseRedirect(_get_default_redirect())
        context['title'] = 'לוגיקה'
        context['next'] = _get_default_redirect()
    else: # POST (full handling is done in UserAuthForm)
        context['username'] = request.POST.get('username','').strip()
        context['password'] = request.POST.get('password','')
        if _is_id_num_needed(request.POST):
            context['get_id_num'] = True

    return auth_login(
        request,
        redirect_field_name = 'next',
        authentication_form = UserAuthForm,
        extra_context = context
    )

def logout(request):
    logger.info('logout: %s', request.user)
    return auth_logout(request, next_page=_get_default_redirect())

# this is currently unused
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        logger.info('registering new user, data: %s', request.POST)
        if form.is_valid():
            # save the new user
            user = form.save()
            # save user profile
            UserProfile.objects.create(
                user=user,
                group=request.POST['group'],
            )
            # autologin and redirect home
            post = request.POST.copy()
            post['password'] = request.POST['password1']
            post['next'] = _get_default_redirect()
            request.POST = post
            return auth_login(request, redirect_field_name='next')
        else:
            logger.error('form is invalid: %s', form)
    else:
        return HttpResponseRedirect(_get_default_redirect())

class UserAuthForm(AuthenticationForm):

    def __init__(self, request, **kwargs):
        super(UserAuthForm, self).__init__(request, **kwargs)
        self.request = request

    def clean(self, *args, **kwargs):
        if self.request.method == 'POST':
            self._handle_login_post()
        super(UserAuthForm, self).clean(*args, **kwargs)

    def _handle_login_post(self):
        username = self.request.POST.get('username', '').strip()
        password = self.request.POST.get('password', '')
        id_num = self.request.POST.get('id_num')
        logger.info('login post: username=%s', username)
        if username and password:
            # authenticate user through ldap
            _ldap_auth(username, password)
            group_id = auth_ldap.get_user_group_id(username)
            logger.debug('%s: group=%s', username, group_id)
            if not group_id:
                raise ValidationError('אינך רשומ\ה לקורס')
            if _is_id_num_needed(self.request.POST):
                # to prompt the user to input id num
                logger.debug('%s: prompting user for id num', username)
                raise ValidationError('')
            with transaction.atomic():
                user, user_created = User.objects.get_or_create(username=username)
                profile = self._handle_user_profile(user, group_id, id_num)
                logger.debug('%s: user_created=%s, profile=%s', username, user_created, profile)
                if not user.check_password(password):
                    # password has changed
                    logger.debug('%s: changing user password', username)
                    user.set_password(password)
                    user.save()
        else:
            raise ValidationError('נא להזין שם משתמש וסיסמה')

    def _handle_user_profile(self, user, group_id, id_num):
        has_profile = UserProfile.objects.filter(user=user).count() == 1
        if has_profile:
            profile = user.userprofile
            if profile.group != group_id or (id_num is not None and profile.id_num != id_num):
                profile.group = group_id
                profile.id_num = id_num
                profile.save()
        else:
            profile = UserProfile.objects.create(user=user, group=group_id, id_num=id_num)
        return profile

def _is_id_num_needed(post_data):
    if not 'id_num' in post_data:
        user = User.objects.filter(username=post_data.get('username','').strip()).first()
        if not user:
            return True
        else:
            profile = UserProfile.objects.filter(user=user).first()
            if not profile or not profile.id_num:
                return True
    return False

def _ldap_auth(username, password):
    logger.debug('check ldap auth: %s', username)
    if auth_ldap.auth(username, password):
        # ok
        logger.debug('check ldap auth: %s: OK', username)
    else:
        # not ok
        if auth_ldap.user_exists(username):
            # wrong password
            logger.debug('check ldap auth: %s: wrong password', username)
            raise ValidationError('סיסמה שגויה')
        else:
            # wrong username
            logger.debug('check ldap auth: %s: wrong username', username)
            raise ValidationError('שם לא נמצא - יש להזין שם משתמש וסיסמה של האוניברסיטה')
    logger.debug('check ldap auth: %s: done', username)
