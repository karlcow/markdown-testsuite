"""
Shared functionality.
"""

import imp
import os

# Default config values here.
config_file_noext = 'config_local'
config_file = config_file_noext + '.py'
config = dict(
    gfm_oauth_token = '',
    # GFM off by default because it is too slow.
    run_all_disable = ['gfm'],
    timeout = 5
)
try:
    config_custom = imp.load_source(config_file_noext, config_file).config
    config.update(config_custom)
except IOError:
    # Config file not present.
    pass

# Encoding of all out outputs when we can chose it, hopefully equal to most inputs.
encoding = 'utf-8'
in_ext = u".md"
out_ext = u".out"
test_dir = u"tests"
engines_dir = os.path.join(test_dir, u"extensions")

# Output UTF-8 by default.
import sys
reload(sys)
sys.setdefaultencoding(encoding)

def same_basename_on_parent(path):
    path_split = path.split(os.sep)
    return os.sep.join(path_split[0:-2] + [path_split[-1]])

def io_iterator():
    """
    Iterator over all input output pairs of the Original markdown, no engines.

    Each yield returns a 3-tuple `(path, input, output)` where:

    - `path` is the path of the test relative to the `test_dir` and without engine (`.md` or `.out`).
    - `input` and `output` are the content of the input and output files.
    """
    for basename in sorted(os.listdir(test_dir)):
        input_path = os.path.join(test_dir, basename)
        if os.path.isfile(input_path):
            path_noext, ext = os.path.splitext(input_path)
            if ext == in_ext:
                with open(input_path, "r") as input_file:
                    input = input_file.read().decode(encoding)
                output_path = path_noext + out_ext
                with open(output_path, "r") as output_file:
                    output = output_file.read().decode(encoding)
                yield (os.path.splitext(basename)[0], input, output)

def io_iterator_engine(id):
    """
    Iterator over all input output pairs of a given engine.

    Original markdown is not included.
    """
    engine_dir = os.path.join(engines_dir, id)
    for basename in sorted(os.listdir(engine_dir)):
        input_path = os.path.join(engine_dir, basename)
        if os.path.isfile(input_path):
            path_noext, ext = os.path.splitext(input_path)
            if ext == in_ext:
                # Get input
                with open(input_path, "r") as input_file:
                    input = input_file.read().decode(encoding)
                if not input:
                    with open(same_basename_on_parent(input_path), "r") as input_file:
                        input = input_file.read().decode(encoding)
                # Get output
                output_path = path_noext + out_ext
                if not os.path.exists(output_path):
                    output_path = same_basename_on_parent(output_path)
                with open(output_path, "r") as output_file:
                    output = output_file.read().decode(encoding)
                yield (os.path.splitext(basename)[0], input, output)

def get_engine_ids():
    """
    Returns a sorted list of ids of all supported engines
    based on the directories present under the engines directory.
    """
    output = []
    for basename in sorted(os.listdir(engines_dir)):
        path = os.path.join(engines_dir, basename)
        if os.path.isdir(path):
            output.append(basename)
    return output

def io_iterator_all_engines():
    """
    Iterator over all input output pairs of a all engines

    Original markdown is not included.
    """
    for id in get_engine_ids():
        for io in io_iterator_engine(id):
            yield io
