import ldap
import re

from logic.models import GlobalSettings

##############################################################################################
# settings

ENDPOINT = 'ldap://ldap.tau.ac.il'
USER_OU = ['Students', 'Staff']

def enabled():
    return GlobalSettings.get().ldap_enabled

def course_id():
    return GlobalSettings.get().course_id[:-2]

def course_main():
    return GlobalSettings.get().course_id[-2:]

def course_groups():
    return ['%02d' % i for i in range(2,int(GlobalSettings.get().max_group_id)+1)]

def get_default_group_id():
    return course_main()

##############################################################################################

##############################################################################################
# functionality

def connect():
    if enabled():
        return ldap.initialize(ENDPOINT)

def auth(uname, pw):
    if not enabled():
        return True
    success = False
    try:
        user_ou = get_user_ou(uname)
        if user_ou:
            connect().simple_bind_s('cn=%s,ou=%s,o=TAU' % (uname, get_user_ou(uname)), pw.encode('utf-8'))
            success = True
    except ldap.INVALID_CREDENTIALS:
        pass
    return success

def user_exists(uname):
    if not enabled():
        return True
    for ou in USER_OU:
        if user_exists_in_ou(uname, ou):
            return True
    return False

def user_exists_in_ou(uname, ou):
    if not enabled():
        return True
    result = connect().search_s('ou=%s,o=TAU' % ou, ldap.SCOPE_SUBTREE, 'cn=%s' % uname)
    return len(result) > 0

def user_exists_in_course(uname, course_id=course_id(), group_id=course_main()):
    if not enabled():
        return True
    students = list_students(course_id, group_id)
    return uname in students or uname.lower() in students or uname.upper() in students

def get_user_group_id(uname, course_id=course_id()):
    if not enabled():
        return course_main()
    for group_id in course_groups() + [course_main()]:
        if user_exists_in_course(uname, course_id, group_id):
            return group_id

def get_all_user_group_ids(uname, course_id=course_id()):
    if not enabled():
        return course_main()
    return [
        group_id for group_id in course_groups() + [course_main()]
        if user_exists_in_course(uname, course_id, group_id)
    ]

def list_students(course_id=course_id(), group_id=course_main()):
    if not enabled():
        return []
    result = connect().search_s('ou=Courses,o=TAU', ldap.SCOPE_SUBTREE, 'cn=%s%s' % (course_id, group_id))
    return {_extract_cn(entry) for entry in result[0][1]['member']}

def get_user_ou(uname):
    if enabled():
        for ou in USER_OU:
            if user_exists_in_ou(uname, ou):
                return ou

def _extract_cn(entry):
    match = re.findall('cn=(\S+?),', entry)
    return match[0] if match else None

##############################################################################################
