#!/usr/bin/env python

import argparse
import itertools

import md_testsuite

output_path = u"all.tmp.md"

parser = argparse.ArgumentParser(
    description="Concatenate all input output pairs into a single file.",
    epilog=r"""The output file is: `{output_path}`. It is already gitignored.

The output format is:

    # Path

    Input

    ---

    Output

    # Path2

    ...
""" % {output_path:output_path},                   # f contains command name.
    formatter_class=argparse.RawTextHelpFormatter, # Keep newlines.
)
args = parser.parse_args()

# Clear the output path.
with open(output_path, "w") as output_file: pass
for path, input, output in itertools.chain(md_testsuite.io_iterator(),
        md_testsuite.io_iterator_all_engines()):
    with open(output_path, "a") as output_file:
        output_file.write("# {0}\n\n{1}\n\n---\n\n{2}\n\n".format(path, input, output))
