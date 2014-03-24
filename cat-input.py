#!/usr/bin/env python

"""
Concatenate all markdown input into a single file.
"""

import os

output_path=u"inputs.tmp.md"
test_dir=u"tests"

with open(output_path, "w") as output_file: pass
for root, dirs, files in os.walk(test_dir):
    dirs.sort()
    files.sort()
    for basename in files:
        path = os.path.join(root, basename)
        path_noext, ext = os.path.splitext(path)
        if ext == ".md":
            with open(path, "r") as input_file:
                input_content = input_file.read()
            if input_content:
                input_content = "# {0}\n\n{1}\n\n".format(path_noext[(len(test_dir)+1):], input_content)
                with open(output_path, "a") as output_file:
                    output_file.write(input_content)
