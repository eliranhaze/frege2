
if __name__ == '__main__':

    skipstart = '// @@skipstart'
    skipend = '// @@skipend'
    expstart = 'function '
    expend = '// @@export'
    exports = []

    def check_export(line):
        if line.startswith(expstart) and expend in line:
            exports.append(line)
 
    def export(w, line):
        name = line[line.index(expstart)+len(expstart):line.index('(')]
        w.write('exports.%s = %s;\n' % (name, name))

    with open('deduction2.js', 'w') as w:
        with open('deduction.js') as r:
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
