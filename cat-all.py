#!/usr/bin/env python

"""
Concatenate all input output pairs into a single markdown file with format:

# Path

Input

---

Output

# Path2

...
"""

import itertools

import md_testsuite

output_path = u"all.tmp.md"

assert [i for i in itertools.chain(xrange(2), xrange(2))] == [0, 1, 0, 1]

with open(output_path, "w") as output_file: pass
for path, input, output in itertools.chain(md_testsuite.io_iterator(),
        md_testsuite.io_iterator_all_engines()):
    with open(output_path, "a") as output_file:
        output_file.write("# {0}\n\n{1}\n\n---\n\n{2}\n\n".format(path, input, output))
