Montmark
========

*A lightweight, fast, pure-Python Markdown parser*

> Small. Walkable. Full of shortcuts. Sketched on a Parisian hill.

## Introduction

Montmark turns Markdown into HTML. It is more than 90% compliant with CommonMark specification.

> WORK IN PROGRESS! This is ALPHA quality software. Do not use it in production!

## Plan

- Continue ongoing updates progressively improving CommonMark compliance toward to near 100%
- Add support for GitHub tables
- Add streaming mode for low-memory processing of very large files
- Optimize

## Installation

### As a package from PyPI

    pip install montmark

### As a standalone file

file `montmark.py` can be downloaded from GitHub or extracted from the PyPI package and used as a standalone script or module.

## CLI

One of these for package:

    montmark FILE
    python3 -m montmark FILE

For standalone script:

    python3 montmark.py FILE

the `FILE` argument may be a file path or `-` for standard input (stdin).

## API

```Python
>>> import montmark
>>> html_string = montmark.convert(markdown_string)
```

## Preliminary benchmark

> Done with bench script and syntax.md sample from Mistletoe, on a 14th gen Intel Core i5 running Ubuntu 24.04 

| Parser                      | Execution Time (s) | Throughput (MB/s) |
| --------------------------- | ------------------ | ----------------- |
| montmark    0.0.6           |              4.85  |              5.73 |
| markdown_it 4.2.0           |              5.61  |              4.95 |
| mistune     3.2.1           |              6.53  |              4.25 |
| mistletoe   1.5.1           |              7.30  |              3.81 |
| marko       2.2.3           |             23.30  |              1.19 |

## CommonMark compliance

| Section                                       |    OK | Total |  % OK | Discrepancies                                 |
| --------------------------------------------- | ----- | ----- | ----- | --------------------------------------------- |
| Tabs                                          |    11 |    11 |  100% |                                               |
| Backslash escapes                             |    13 |    13 |  100% |                                               |
| Entity and numeric character references       |    17 |    17 |  100% |                                               |
| Precedence                                    |     1 |     1 |  100% |                                               |
| Thematic breaks                               |    19 |    19 |  100% |                                               |
| ATX headings                                  |    18 |    18 |  100% |                                               |
| Setext headings                               |    26 |    27 |   96% | 91                                            |
| Indented code blocks                          |    11 |    12 |   91% | 109                                           |
| Fenced code blocks                            |    29 |    29 |  100% |                                               |
| HTML blocks                                   |    38 |    44 |   86% | 148,174,175,187,190,191                       |
| Link reference definitions                    |    23 |    27 |   85% | 201,208,209,210                               |
| Paragraphs                                    |     8 |     8 |  100% |                                               |
| Blank lines                                   |     1 |     1 |  100% |                                               |
| Block quotes                                  |    21 |    25 |   84% | 235,237,238,252                               |
| List items                                    |    47 |    48 |   97% | 300                                           |
| Lists                                         |    22 |    26 |   84% | 312,313,319,326                               |
| Inlines                                       |     1 |     1 |  100% |                                               |
| Code spans                                    |    22 |    22 |  100% |                                               |
| Emphasis and strong emphasis                  |   126 |   132 |   95% | 412,430,445,461,469,470                       |
| Links                                         |    79 |    90 |   87% | 520,523,533,541,545,546,556,559,568,569,571   |
| Images                                        |    17 |    22 |   77% | 574,575,587,590,593                           |
| Autolinks                                     |    18 |    19 |   94% | 610                                           |
| Raw HTML                                      |    16 |    20 |   80% | 616,619,629,632                               |
| Hard line breaks                              |    14 |    15 |   93% | 644                                           |
| Soft line breaks                              |     2 |     2 |  100% |                                               |
| Textual content                               |     3 |     3 |  100% |                                               |
| ALL                                           |   603 |   652 |   92% |                                               |

## Open-Source, not Open-Contribution yet

Montmark is [MIT licensed](LICENCE) but is currently closed to contributions.
> Personal note: this is a pet projet of mine and my time is limited. First I need to focus on my roadmap (new features and refactoring) and then I will happily accept contributions when everything is a little more stabilised. 