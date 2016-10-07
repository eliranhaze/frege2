from django.core.management.base import BaseCommand

from frege import auth_ldap

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('--test', action='store_true', default=False)

    def handle(self, *args, **options):
        print 'ldap info'
        print '---------'
        print 'Enabled = %s' % auth_ldap.enabled()
        print 'Course id = %s' % auth_ldap.course_id()
        print 'Course main = %s' % auth_ldap.course_main()
        print 'Course groups = %s' % auth_ldap.course_groups()
        if options['test']:
            self.test()

    def test(self):
        test_user = 'eliranhaziza'
        print 'TESTING'
        print '- listing students...', len(auth_ldap.list_students())
        print '- user %s exists:' % test_user, auth_ldap.user_exists(test_user) 
        print '- user %s group:' % test_user, auth_ldap.get_user_group_id(test_user) 
        print '- user %s ou:' % test_user, auth_ldap.get_user_ou(test_user) 
        print 'DONE'
