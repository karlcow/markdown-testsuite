#!/usr/bin/env python

import argparse
import distutils.spawn
from htmlentitydefs import name2codepoint
from HTMLParser import HTMLParser
import itertools
import json
import re
import subprocess
import sys
import time
import urllib2

import md_testsuite
from md_testsuite import config

significant_attrs = ["alt", "href", "src"]
normalize_whitespace_re = re.compile('\s+')
class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.last = "starttag"
        self.in_pre = False
        self.output = u""
    def handle_data(self, data):
        if self.in_pre:
            self.output += data
        else:
            data = normalize_whitespace_re.sub(' ', data)
            data_strip = data.strip()
            if (self.last == "ref") and data_strip and data[0] == " ":
                self.output += " "
            self.data_end_in_space_not_empty = (data[-1] == ' ' and data_strip)
            self.output += data_strip
            self.last = "data"
    def handle_endtag(self, tag):
        if tag == "pre":
            self.in_pre = False
        self.output += "</" + tag + ">"
        self.last = "endtag"
    def handle_starttag(self, tag, attrs):
        if tag == "pre":
            self.in_pre = True
        self.output += "<" + tag
        attrs = filter(lambda attr: attr[0] in significant_attrs, attrs)
        if attrs:
            attrs.sort()
            for attr in attrs:
                self.output += " " + attr[0] + "=" + '"' + attr[1] + '"'
        self.output += ">"
        self.last = "starttag"
    def handle_startendtag(self, tag, attrs):
        """Ignore closing tag for self-closing void elements."""
        self.handle_starttag(tag, attrs)
    def handle_entityref(self, name):
        self.add_space_from_last_data()
        self.output += unichr(name2codepoint[name])
        self.last = "ref"
    def handle_charref(self, name):
        self.add_space_from_last_data()
        if name.startswith("x"):
            c = unichr(int(name[1:], 16))
        else:
            c = unichr(int(name))
        self.output += c
        self.last = "ref"
    # Helpers.
    def add_space_from_last_data(self):
        """Maintain the space at: `a <span>b</span>`"""
        if self.last == 'data' and self.data_end_in_space_not_empty:
            self.output += ' '

def normalize_output(html):
    r"""
    Return normalized form of HTML which igores insignificant output differences.

    Multiple inner whitespaces to a single space

        >>> normalize_output("<p>a  \t\nb</p>")
        u'<p>a b</p>'

    Surrounding whitespaces are removed:

        >>> normalize_output("<p> a</p>")
        u'<p>a</p>'

        >>> normalize_output("<p>a </p>")
        u'<p>a</p>'

    TODO: how to deal with the following cases without a full list of the void tags?

        >>> normalize_output("<p>a <b>b</b></p>")
        u'<p>a<b>b</b></p>'

        >>> normalize_output("<p><b>b</b> c</p>")
        u'<p><b>b</b>c</p>'

        >>> normalize_output("<p>a <br></p>")
        u'<p>a<br></p>'

    `pre` elements preserve whitespace:

        >>> normalize_output("<pre>a  \t\nb</pre>")
        u'<pre>a  \t\nb</pre>'

    Self-closing tags:

        >>> normalize_output("<p><br /></p>")
        u'<p><br></p>'

    References are converted to Unicode:

        >>> normalize_output("<p>&lt;</p>")
        u'<p><</p>'

        >>> normalize_output("<p>&#60;</p>")
        u'<p><</p>'

        >>> normalize_output("<p>&#x3C;</p>")
        u'<p><</p>'

        >>> normalize_output("<p>&#x4E2D;</p>")
        u'<p>\u4e2d</p>'

    Spaces around entities are kept:

        >>> normalize_output("<p>a &lt; b</p>")
        u'<p>a < b</p>'

        >>> normalize_output("<p>a&lt;b</p>")
        u'<p>a<b</p>'

    Most attributes are ignored:

        >>> normalize_output('<p id="a"></p>')
        u'<p></p>'

    Critical attributes are considered and sorted alphabetically:

        >>> normalize_output('<a href="a"></a>')
        u'<a href="a"></a>'

        >>> normalize_output('<img src="a" alt="a">')
        u'<img alt="a" src="a">'
    """
    parser = MyHTMLParser()
    parser.feed(html)
    parser.close()
    return parser.output

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

class Engines(object):
    """
    All nested classes of this class represent markdown engines and implement the static methods:

    - available
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
            return distutils.spawn.find_executable(cls.command[0])
        @classmethod
        def get_output(cls, input):
            return stdin_stdout_get_output(cls.command, input)

    class blackfriday(CommandEngine): command = ['blackfriday']
    class hoedown(CommandEngine): command = ['hoedown', '--all-block', '--all-span']
    class kramdown(CommandEngine): command = ['kramdown']
    class lunamark(CommandEngine): command = ['lunamark']
    class markdown_pl(CommandEngine): command = ['Markdown.pl']
    class marked(CommandEngine): command = ['marked']
    class maruku(CommandEngine): command = ['maruku']
    class md2html(CommandEngine): command = ['md2html']
    class multimarkdown(CommandEngine): command = ['multimarkdown']
    class pandoc(CommandEngine): command = ['pandoc']
    class rdiscount(CommandEngine): command = ['rdiscount']
    class redcarpet(CommandEngine): command = ['redcarpet']

class TestResult(object):
    """
    Encapsulates test results for one engine.
    """
    def __init__(self, error_io_string="", summary_one_line=""):
        self.error_io_string = error_io_string
        self.summary_one_line = summary_one_line

    def __add__(self, other):
        return TestResult(
            self.error_io_string + other.error_io_string,
            self.summary_one_line + other.summary_one_line,
        )

def stdout_and_string(old, new):
    """
    Add new string to old string, print it to stdout and flush.

    Returns new concatanted string.
    """
    sys.stdout.write(new)
    sys.stdout.flush()
    return old + new

def run_tests(io_iterator, engine_name, l, args):
    """
    Run tests for one engine for the given input output pairs.

    Outputs progress bar while running the tests.

    args are used to filter which tests will be run.
    """
    total = 0
    errors = 0
    start_time = time.time()
    error_io_string = ""
    summary_one_line = ""
    summary_one_line = stdout_and_string(summary_one_line, "{:<{l}} |".format(engine_name, l=l))
    engine = getattr(Engines, engine_name)
    io_iterator = itertools.ifilter(lambda io: args.filter_string in io[0], io_iterator)
    for path, input, expected_output in io_iterator:
        total += 1
        if not args.number or total == args.number:
            output = engine.get_output(input)
            normalized_output = normalize_output(output)
            normalized_expected_output = normalize_output(expected_output)
            if normalized_output == normalized_expected_output:
                summary_one_line = stdout_and_string(summary_one_line, ".")
            else:
                errors += 1
                summary_one_line = stdout_and_string(summary_one_line, "F")
                error_io_string += (
                    '# ' + path + ' | #' + unicode(total) + ' | ' + engine_name + '\n'
                    + "=" * 70 + '\n'
                    + '\n'
                    + repr(input) + '\n'
                    + '\n'
                    + 'Normalized actual / expected:' + '\n'
                    + repr(normalized_output) + '\n'
                    + repr(normalized_expected_output) + '\n'
                    + '\n'
                    + 'Raw actual / expected:' + '\n'
                    + repr(output) + '\n'
                    + repr(expected_output) + '\n'
                    + '\n'
                )
    elapsed_time = time.time() - start_time
    if total == 0:
        percent = 0
    else:
        percent = int(errors/float(total)*100)
    summary_one_line = stdout_and_string(
        summary_one_line,
        "| {:>6.2f}s {:4} {:4} {:>3}%\n".format(elapsed_time, total, errors, percent)
    )
    return TestResult(error_io_string, summary_one_line)

def format_error_ios_and_summaries(test_result, test_result_extension):
    return (
        '\n' + test_result.error_io_string + test_result_extension.error_io_string
        + test_result.summary_one_line + "\nExtensions:\n\n"
        + test_result_extension.summary_one_line
    )

if __name__ == "__main__":
    all_engine_names = md_testsuite.get_engine_ids()
    parser = argparse.ArgumentParser(
        description="Run markdown tests.",
        epilog=r"""# Definitions

- enabled: engines may be disabled through the file `{config_file}`.
- available: engines are said to be available if they can be used if the user wishes.

    For command line utilies, this means that they are installed and in `PATH`.

    For REST APIs, this means that the internet connection and the server are working.

# Normalization

In order for output comparison to be meaningful, HTML outputs must be normalized
before comparison.

The chosen normalization is heuristic, and goes beyond simple DOM tree transformation:
its goal is to normalize outputs that render equally in most browsers as equal,
and different DOM trees may render exactly the same on most browsers.

Normalized aspects include:

- convert multiple consecutive whitespaces to a single space
- sort attributes alphabetically
- remove attributes such as `id` or `class` which are added by many engines
- self-closing tags are transformed into regular tags, as they are equivalent in HTML5
- references are converted to Unicode

# Most useful invocations

Run all enabled and available tests with summarized error format:

    {f}

Each summary output line is of the form:

    multimarkdown |.F..|   0.60s  4   1  25%

Where:

- `.` indicates a passing test
- `F` indicates a failing test
- `0.60s` is the wall time used to run all commands
- `4` is the total number of tests
- `1` is the total number of failing tests
- `25%` is the percentage of failing tests

Run all tests for the given engine:

    {f} multimarkdown

Run only tests which contain a literal string in the name:

    {f} -s string
    {f} -s string multimarkdown
""".format(f=sys.argv[0], config_file=md_testsuite.config_file),   # f contains command name.
        formatter_class=argparse.RawTextHelpFormatter,                 # Keep newlines.
    )
    parser.add_argument(
        "-a",
        "--enable-all",
        action="store_true",
        default=False,
        help="Enable all engines for a single command."
    )
    parser.add_argument(
        "-l",
        "--list-engines",
        action="store_true",
        default=False,
        help="List engines. If given, overrides all other options and nothing else is done."
    )
    parser.add_argument(
        "-n",
        "--number",
        default=None,
        type=int,
        help="""Only run the test with given number.
The number of a test is affected by filtering options such as `-s`."""
    )
    parser.add_argument(
        "-s",
        "--filter-string",
        default="",
        help="""Only run tests whose names contain the given literal string.
If given, output expected / actual IO even if `engine` was not given."""
    )
    parser.add_argument(
        'engine',
        choices=all_engine_names,
        nargs='?',
        help="""If given, only run tests for this engine even is disabled, and print actual / expected IO for each failing test.
Else, run all engines which are both enabled and available, and print only summarized output."""
    )
    args = parser.parse_args()

    disabled_by_conf = config['run_all_disable']
    if args.enable_all:
        enabled_engine_names = all_engine_names
    else:
        enabled_engine_names = filter(lambda e: not e in disabled_by_conf, all_engine_names)
    enabled_and_available_engine_names = filter(lambda e: getattr(Engines, e).available(), enabled_engine_names)
    enabled_and_not_available_engine_names = filter(lambda x: not x in enabled_and_available_engine_names, enabled_engine_names)

    if args.list_engines:
        print "All:                   {}\n" \
              "Enabled:               {}\n" \
              "Available:             {}\n" \
              "Enabled and Available: {}".format(
              ", ".join(all_engine_names),
              ", ".join(enabled_engine_names),
              ", ".join(filter(lambda e: getattr(Engines, e).available(), all_engine_names)),
              ", ".join(enabled_and_available_engine_names),
        )
    else:
        if args.engine:
            engine_name = args.engine
            test_result = run_tests(md_testsuite.io_iterator(), engine_name, len(engine_name), args)
            print "\nExtensions:\n"
            test_result_extension = run_tests(md_testsuite.io_iterator_engine(engine_name),
                    engine_name, len(engine_name), args)
            print format_error_ios_and_summaries(test_result, test_result_extension)
        else:
            if disabled_by_conf:
                print "Disabled engines:              {}".format(", ".join(disabled_by_conf))
                newline = True
            if enabled_and_not_available_engine_names:
                print "Enabled engines not available: {}".format(", ".join(enabled_and_not_available_engine_names))
                newline = True
            if newline:
                print
            if enabled_and_available_engine_names:
                l = len(max(enabled_and_available_engine_names, key=len))
                test_result = TestResult()
                for engine_name in enabled_and_available_engine_names:
                    test_result += run_tests(md_testsuite.io_iterator(), engine_name, l, args)
                print "\nExtensions:\n"
                test_result_extension = TestResult()
                for engine_name in enabled_and_available_engine_names:
                    test_result_extension += run_tests(md_testsuite.io_iterator_engine(engine_name), engine_name, l, args)
                if args.filter_string:
                    print format_error_ios_and_summaries(test_result, test_result_extension)
            else:
                print "No engines are enabled. Install or enable some."
