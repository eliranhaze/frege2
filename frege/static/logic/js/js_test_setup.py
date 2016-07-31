import os
 
skipstart = '// @@skipstart'
skipend = '// @@skipend'
expstarts = {
    'function ': '(',
    'var ': ' = ',
}
expend = '// @@export'

def process(name):
    exports = []

    def check_export(line):
        for expstart in expstarts:
            if line.startswith(expstart) and expend in line:
                exports.append(line)
 
    def export(w, line):
        for expstart in expstarts:
            if line.startswith(expstart):
                name = line[line.index(expstart)+len(expstart):line.index(expstarts[expstart])]
                w.write('exports.%s = %s;\n' % (name, name))

    new_filename = '%s2.js' % name
    with open(new_filename, 'w') as w:
        with open('%s.js' % name) as r:
            skip = False
            for line in r.read().splitlines():
                check_export(line)
                if line.startswith(skipstart):
                    skip = True
                    w.write('// @@ skipped\n')
                    continue
                if skip:
                    if line.startswith(skipend):
                        skip = False
                        continue
                if not skip:
                    w.write(line+'\n')
        w.write('\n// @@ exports\n')
        for exp in exports:
            export(w, exp)

    return new_filename

if __name__ == '__main__':
    modules = ['formula', 'deduction']
    testsfile = 'testslib.js'
    open(testsfile, 'w').close()
    for module in modules:
        filename = process(module)
        with open(filename) as r:
            with open(testsfile, 'a') as w:
                w.write(r.read())
        os.remove(filename)

