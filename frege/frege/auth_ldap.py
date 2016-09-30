import ldap

ENABLED = True
ENDPOINT = 'ldap://ldap.tau.ac.il'

USER_OU = ['Students', 'Staff']

COURSE_ID = '06181012'
COURSE_MAIN = '01'
COURSE_GROUPS = ['%02d' % i for i in range(2,9+1)]

def connect():
    if ENABLED:
        return ldap.initialize(ENDPOINT)

def auth(uname, pw):
    if not ENABLED:
        return True
    success = False
    for ou in USER_OU:
        try:
            connect().simple_bind_s('cn=%s,ou=%s,o=TAU' % (uname, ou), pw)
            success = True
            break
        except ldap.INVALID_CREDENTIALS:
            pass
    return success

def user_exists(uname):
    if not ENABLED:
        return True
    for ou in USER_OU:
        result = connect().search_s('ou=%s,o=TAU' % ou, ldap.SCOPE_SUBTREE, 'cn=%s')
        if result:
            return True
    return False

def list_students(course_id=COURSE_ID, group_id=COURSE_MAIN):
    if not ENABLED:
        return []
    result = connect().search_s('ou=Courses,o=TAU', ldap.SCOPE_SUBTREE, 'cn=%s%s' % (course_id, group_id))
    return result
