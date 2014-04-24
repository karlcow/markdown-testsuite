#!/usr/bin/env python

"""
Run markdown tests.

The following invocations are possible:

Run tests for all engines and output summarized results:

    run-tests.py

Only engines that are both detected available (e.g. program installed or no internet conection for GFM)
and are not disabled by `md_testsuite.config['run_all_disable']` will be run.

Run tests for a given engine with detailed error output:

    run-tests.py <engine>

For each engine, tests under `extensions/<engine>` are also run.
"""

import distutils.spawn
import itertools
import json
import subprocess
import sys
import time
import urllib2

try:
    import bs4
except ImportError:
    print 'ERROR: Missing dependencies. Install with:\n\nsudo pip install -r requirements.txt'
    sys.exit(1)

import md_testsuite
from md_testsuite import config

def dom_normalize(html):
    """
    Returns normalized form of HTML.

    Two DOM equivalent HTMLs must have the same normalized form.
    """
    soup = bs4.BeautifulSoup(html)
    return soup.prettify()

def stdin_stdout_get_output(command, stdin):
    """
    Convenience method for engines that take input on stdin and output to stdout.
    """
    process = subprocess.Popen(
        command,
        shell  = False,
        stdin  = subprocess.PIPE,
        stdout = subprocess.PIPE,
        stderr = subprocess.PIPE,
        universal_newlines = True
    )
    stdout, stderr = process.communicate(stdin)
    return stdout.decode(md_testsuite.encoding)

def command_present(command):
    return distutils.spawn.find_executable(command)

class Engines(object):
    """
    All nested classes of this class represent markdown engines and implement the static methods:

    - present
    - get_output

    The names of those classes must correspond exactly to directory names under `extensions/`.
    """

    class gfm(object):
        """
        You **must** be authenticated to use this because this test suite has more than 50 tests.
        <http://developer.github.com/v3/#rate-limiting>
        - authenticated: 60 requests per hour
        - unauthenticated requests: 5000 requests per hour
        """

        url = 'https://api.github.com/markdown?access_token=' + config['gfm_oauth_token']

        @classmethod
        def available(cls):
            if not config['gfm_oauth_token']:
                return False
            data = '{"text":"a","mode":"gfm","context":"github/gollum"}'
            req = urllib2.Request(cls.url, data)
            try:
                response = urllib2.urlopen(req, timeout = config['timeout'])
            except urllib2.URLError, e:
                return False
            return True

        @classmethod
        def get_output(cls, input):
            data = '{{"text":{},"mode":"gfm","context":"github/gollum"}}'.format(json.dumps(input))
            req = urllib2.Request(cls.url, data)
            try:
                response = urllib2.urlopen(req, timeout = config['timeout'])
            except urllib2.URLError, e:
                return 'CONNEXION ERROR: ' + str(e)
            return response.read().decode(md_testsuite.encoding)

    class CommandEngine(object):
    	"""
    	Base class for engines which use a command in PATH.
    	"""
        @classmethod
        def available(cls):
            return command_present(cls.__name__)
        @classmethod
        def get_output(cls, input):
            return stdin_stdout_get_output([cls.__name__], input)

    class kramdown(CommandEngine):
        @classmethod                                                                                                                            
        def get_output(cls, input):                                                                                                             
            return stdin_stdout_get_output([cls.__name__, '--no-auto-ids'], input)                                                              
    	
    class multimarkdown(CommandEngine): pass
    class pandoc(CommandEngine): pass
    class redcarpet(CommandEngine): pass

def on_ok_single(path, input, output, expected_output):
    sys.stdout.write('.')
    sys.stdout.flush()

def on_error_single(path, input, output, expected_output):
    print
    print '# ' + path
    print "=" * 70
    print
    print input
    print
    print ("-" * 35) + ' output:'
    print
    print output
    print
    print ("-" * 35) + ' expected:'
    print
    print expected_output
    print
    print "=" * 70
    print

def on_ok_many(path, input, output, expected_output):
    """
    On error when a multiple engines are being tested.
    """
    sys.stdout.write(' ')
    sys.stdout.flush()

def on_error_many(path, input, output, expected_output):
    """
    On error when a multiple engines are being tested.
    """
    sys.stdout.write('F')
    sys.stdout.flush()

def run_tests(io_iterator, get_output, on_error, on_ok=lambda *args:None):
    """
    Run tests for one engine for the given input output pairs.
    """
    total = 0
    errors = 0
    start_time = time.time()
    for path, input, expected_output in io_iterator:
        total += 1
        output = get_output(input)
        normalized_output = dom_normalize(output)
        normalized_expected_output = dom_normalize(expected_output)
        if normalized_output == normalized_expected_output:
            on_ok(path, input, normalized_output, normalized_expected_output)
        else:
            errors += 1
            on_error(path, input, normalized_output, normalized_expected_output)
    elapsed_time = time.time() - start_time
    return elapsed_time, total, errors

def test_summarize(engine_name, io_iterator, l):
    """
    Test given IO pairs for given engine with summarized output.
    """
    engine = getattr(Engines, engine_name)
    sys.stdout.write("{:<{l}} |".format(engine_name, l=l))
    sys.stdout.flush()
    elapsed_time, total, errors = run_tests(io_iterator, engine.get_output, on_error_many, on_ok_many)
    if total != 0:
        percent = int(errors/float(total)*100)
    else:
        percent = 0
    sys.stdout.write("| {:>6.2f}s {:4} {:4} {:>3}%\n".format(elapsed_time, total, errors, percent))

if len(sys.argv) == 1:
    all_engine_names = md_testsuite.get_engine_ids()
    disabled_by_conf = config['run_all_disable']
    enabled_engine_names = filter(lambda e: not e in disabled_by_conf, all_engine_names)
    available_engine_names = filter(lambda e: getattr(Engines, e).available(), enabled_engine_names)
    not_available_engine_names = filter(lambda x: not x in available_engine_names, enabled_engine_names)

    newline = False
    if disabled_by_conf:
        print "Engines disabled by configuration: {}".format(", ".join(disabled_by_conf))
        newline = True
    if not_available_engine_names:
        print "Enabled engines not available:     {}".format(", ".join(not_available_engine_names))
        newline = True
    if newline:
        print

	if available_engine_names:
		l = len(max(available_engine_names, key=len))
		for engine_name in available_engine_names:
			test_summarize(engine_name, md_testsuite.io_iterator(), l)
		print "\nExtensions:\n"
		for engine_name in available_engine_names:
			test_summarize(engine_name, md_testsuite.io_iterator_engine(engine_name), l)
	else:
		print "No engines are enabled. Install or enable some from config_local.py"
else:
    engine_name = sys.argv[1]
    engine = getattr(Engines, engine_name)
    if engine.available():
        io_iterator = itertools.chain(md_testsuite.io_iterator(), md_testsuite.io_iterator_engine(engine_name))
        elapsed_time, total, errors = run_tests(io_iterator, engine.get_output, on_error_single, on_ok_single)
        labels = ["wall time", "total tests", "errors", "error percent"]
        values = [elapsed_time, total,         errors,   int(errors/float(total)*100)]
        sys.stdout.write("\n{:<{l}}{:.2f}s\n{:<{l}}{}\n{:<{l}}{}\n{:<{l}}{}%\n".format(
            *[x for t in zip(labels,values) for x in t],
            l=len(max(labels, key=len)) + 2
        ))
    else:
        print "Engine not available."
        sys.exit(1)

