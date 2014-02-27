# markdown-testsuite

After starting the [W3C Community Group about Markdown](http://www.w3.org/community/markdown), a question has been raised a few times about a test suite for the markdown syntax.

I decided to put together a list of individual files isolating some constructs of the markdown syntax. Some features might be missing, you know the deal. Pull Requests are welcome.

## Markdown Extensions

Markdown extension tests are accepted. Use the following rules:

- place all extension tests under the `test/extensions/ENGINE` directory with filename equal to the feature name
- for each `ENGINE` and add a `README.md` under the engine directory with a link to its specification

where `ENGINE` is either of:

- a command line utility. E.g. `pandoc`, `kramdown`.
- a programming API. E.g. `Redcarpet::Markdown.new()`.
- a programmatically accessible web service. E.g.: GFM via the GitHub API.
- a non programmatically accessible web service. E.g.: Stack Overflow flavored markdown.

To avoid test duplication for common features, use the following rules:

- if file `tests/extensions/ENGINE/FEATURE.md` is empty or not present, use `tests/extensions/FEATURE.md` instead
- if file `tests/extensions/ENGINE/FEATURE.out` not present, use `tests/extensions/FEATURE.out` instead
- for a given `ENGINE`, only features which have either a `.md` or a `.out` are implemented by that engine.
- in case of different outputs for a single feature input, keep directly under `extensions/` only the output case that happens across the most engines

**version**

Only the latest stable version of each `ENGINE` is considered.

**options**

The IO behavior tested is for engine defaults, without any options (command line options, extra JSON parameters, etc.) passed to the engine.

**external state**

Tests that use external state not present in the markdown input shall not be included in this test suite.

For example, what GFM `@user` user tags render to also depends on the state of GitHub's databases (only render to a link if user exists), not only on the input markdown.

### Examples

GFM and the "fenced code block" use the following file structure:

    tests/extensions/gfm/README.md
    tests/extensions/gfm/fenced-code-block.md
    tests/extensions/gfm/fenced-code-block.out

where `README.md` contains:

    https://help.github.com/articles/github-flavored-markdown

To avoid duplication with other engines, if the input / output (normalized to DOM) is the same across multiple engines use:

    tests/extensions/gfm/fenced-code-block.md       [empty]
    tests/extensions/fenced-code-block.md
    tests/extensions/fenced-code-block.out

If the input is the same, and outputs are DOM different, but represent the same idea (e.g. both represent computer code) use:

    tests/extensions/gfm/fenced-code-block.md       [empty]
    tests/extensions/gfm/fenced-code-block.out
    tests/extensions/fenced-code-block.md
    tests/extensions/fenced-code-block.out
