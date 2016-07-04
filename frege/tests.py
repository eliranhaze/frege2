import subprocess

args_list = ['python', 'manage.py', 'test', 'logic']
process=subprocess.Popen(args_list, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
output, errors = process.communicate()
if not errors:
    for o in output.splitlines():
        if 'OK' in o or 'Ran ' in o or 'FAIL' in o:
            print '--- ', o
else:
    print 'ERRORS'
    print errors
