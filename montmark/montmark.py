"""
MIT License

Copyright (c) 2025-2026 Martin D. <desgeeko@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re
import os
import html
from urllib.parse import quote

DEBUG = os.getenv("DEBUG", "0") == "1"

MATCHING = {'"': '"', "'": "'", "(": ")"}
BACKSLASH_ESCAPED =  '`*_{}[]()#+-.!"$%&\',/:;<=>?@^|~\\'

HE = {'<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;'}
HE_TR = str.maketrans(HE)

TAGS_CONDITION_1 = 'pre script style textarea'.split()
TAGS_CONDITION_6 = '''
address article aside base basefont blockquote body caption center col
colgroup dd details dialog dir div dl dt fieldset figcaption figure footer
form frame frameset h1 h2 h3 h4 h5 h6 head header hr html iframe legend li
link main menu menuitem nav noframes ol optgroup option p param search
section summary table tbody td tfoot th thead title tr track ul
'''.split()

SP = ' \xa0\n'
PUNCTUATION = '_-(){}[]"\'.,!?@#$€£'
SEPS = SP + PUNCTUATION

patterns = ['*', '_', '`', '[', '<', '>', '&', '\\', '"']
escaped = [re.escape(pattern) for pattern in patterns]
spans = '|'.join(escaped)
regex = re.compile(spans)


def extract_square(md: str, start: int, stop: int):
    """Extract content between brackets."""
    square_b = -1
    i = start
    while i < stop:
        if square_b < 0:
            if md[i] not in ' ':
                if md[i] == '[':
                    square_b = i
                else:
                    break
        elif square_b >= 0:
            if md[i] == ']' and md[i-1] != '\\':
                return md[square_b+1:i], i+1
        i += 1
    return '', i+1


def extract_destination(md: str, start: int, stop: int):
    """Search for link destination in link_definition."""
    url_b = -1
    first_char = ''
    i = start
    while i < stop:
        if not first_char:
            if md[i] not in ' \t\n':
                first_char = md[i]
                url_b = i
        elif first_char == '<':
            if md[i] == '>':
                return html.unescape(md[url_b+1:i]), '<>', i+1
        else:
            if md[i] in ' \n':
                return md[url_b:i], '', i
        i += 1
    if url_b:
        return md[url_b:i], '', i
    else:
        return '', None, i


def extract_title(md: str, start: int, stop: int):
    """Search for title in link definition."""
    title_b = -1
    first_char = ''
    i = start
    while i < stop:
        if not first_char:
            if md[i] in MATCHING:
                first_char = md[i]
                title_b = i
        else:
            if md[i] == MATCHING[first_char]:
                return (md[title_b+1:i], i)
        i += 1
    return '', i


def check_link_def(md, start, eol, search = "SQUARE"):
    """Dedicated parsing of links."""
    i = i0 = start
    res = {}
    link_id = url = title = None
    url_b = url_e = 0
    id_b = id_e = 0
    title_b = 0
    brackets = title_m = ''
    if search == "SQUARE":
        if md[i] not in ' [':
            return None, None, None, -1
        square, i = extract_square(md, i, eol)
        if square and md[i] == ':':
            link_id = square
            i += 1
        else:
            return None, None, None, -1
        search = "URL"
    if search == "URL":
        url, typ, i = extract_destination(md, i, eol)
        if not typ and not url:
            return link_id, None, None, eol
        if md[i] not in " \t\n":
            return None, None, None, eol
        search = "TITLE"
    if search == "TITLE":
        title, i = extract_title(md, i, eol)
        if title:
            f = indentation(md, i+1, eol)[1]
            if f < eol:
                return None, None, None, eol
    return (link_id, url, html.unescape(title), eol)


def check_setext(md: str, start = 0):
    """Dedicated detection of setext headers."""
    tok = ''
    nb = 0
    i = start
    sp = 0
    trail = False
    c = md.find('\n', i)
    eol = c if c != -1 else len(md)
    while i < eol:
        if sp > 3:
            return False, -1
        if not tok:
            if md[i] in '=-':
                tok = md[i]
                nb = 1
            elif md[i] == ' ':
                sp += 1
            else:
                return False, -1
            i += 1
            continue
        if tok and md[i] in ' \t':
            trail = True
        if trail and md[i] not in ' \t':
            return False, -1
        elif md[i] == tok:
            nb += 1
        i += 1
    res = tok if nb >= 1 else False
    return res, eol


def check_hr(md: str, start = 0):
    """Dedicated detection of horizontal rule."""
    toks = ''
    i = start
    nb_spc = 0
    c = md.find('\n', i)
    eol = c if c != -1 else len(md)
    while i < eol:
        if not toks:
            if md[i] in '*_-':
                toks = md[i]
            elif md[i] == ' ':
                nb_spc += 1
            elif md[i] == '\t':
                nb_spc += 4
            else:
                return False, -1
            if nb_spc >= 4:
                return False, -1
            i += 1
            continue
        if md[i] not in ' \t' and md[i] != toks[0]:
            return False, -1
        elif md[i] in toks:
            toks += md[i]
        elif md[i] == ' ':
            pass
        i += 1
    res = True if len(toks) >= 3 else False
    return res, eol


def check_tag(md:str, start, stop):
    """."""
    i = start+1
    zone = 'in_main'
    while i < stop-1:
        if zone == 'in_main':
            if not (md[i].isalpha() or md[i].isdigit() or md[i] in ' :-.=/'):
                return False
            if md[i] == '=':
                i += 1
                if md[i] == '"':
                    zone = 'in_double'
                elif md[i] == "'":
                    zone = 'in_single'
                else:
                    return False
        elif zone == 'in_single':
            if md[i] == '"':
                return False
        elif zone == 'in_double':
            if md[i] == "'":
                return False
        i += 1
    return True


def check_html_block(md: str, start, stop):
    """Dedicated detection of html block."""
    i = start
    ends = False
    cond_1 = False
    cond_6 = False
    cond_7 = False
    for t in TAGS_CONDITION_1:
        l = len(t)
        if i+l < stop and md[i+1:i+l+1].lower() == t:
             if md[i+1+l] in ' \t>\n':
                cond_1 = True
    for t in TAGS_CONDITION_6:
        l = len(t)
        closing = md[i+1] == '/'
        if i+l+1 < stop and (md[i+1:i+l+1].lower() == t or (closing and md[i+2:i+l+2].lower() == t)):
             if not closing and md[i+1+l] in ' \t>\n':
                cond_6 = True
             elif closing and md[i+2+l] in ' \t>\n':
                cond_6 = True
    b = md.find('>', i, stop)
    if b > i+1 and (md[i+1].isalpha() or md[i+1] == '/' and md[i+2].isalpha()):
        _, c, _, _ = indentation(md, b+1)
        if (b == stop or c == stop) and ':' not in md[i:stop] and '@' not in md[i:stop]:
            cond_7 = True
    if cond_1:
        condition = 1
        line = md[i:stop]
        for t in TAGS_CONDITION_1:
            if '</' + t + '>' in line.lower():
                ends = True
                break
    elif i+4 < len(md) and md[i:i+4] == '<!--':
        condition = 2
        if md.find('-->', i, stop) > -1:
            ends = True
    elif i+2 < len(md) and md[i:i+2] == '<?':
        condition = 3
        if md.find('-->', i, stop) > -1:
            ends = True
    elif i+3 < len(md) and md[i:i+2] == '<!' and md[i+2].isalpha():
        condition = 4
        if md.find('-->', i, stop) > -1:
            ends = True
    elif i+9 < len(md) and md[i:i+9] == '<![CDATA[':
        condition = 5
        if md.find('-->', i, stop) > -1:
            ends = True
    elif cond_6:
        condition = 6
    elif cond_7:
        if check_tag(md, i, stop):
            condition = 7
        else:
            return None
    else:
        return None
    return (condition, ends)


def indentation(md: str, start: int, extra: int = 0) -> tuple:
    """Find & expand spaces and tabs."""
    i = start
    found = False
    w = 4 if extra else 0
    while i < len(md):
        found = True if not found and md[i] in ' \t' else found
        if md[i] == ' ':
            w += 1
        elif md[i] == '\t':
            w += 4 - (w % 4)
        else:
            break
        i += 1
    return start, i, found, w - extra


def prefix(md: str, start: int = 0) -> tuple:
    """Isolate digits at start."""
    i = start
    seq, w = '', 0
    while i < len(md):
        if not seq and md[i] in '#`~':
            seq = md[i]
        elif not seq and md[i] in '1234567890':
            seq = 'digits'
        if seq == 'digits' and md[i] in '1234567890':
            w += 1
        elif seq == '#' and md[i] == '#':
            w += 1
        elif seq in '`~' and md[i] in '`~':
            w += 1
        else:
            return start, i, seq, w
        i += 1


def html_text(element: str, content, params, last):
    """Prepare html segments but keep them in a list for future join."""
    if element == 'span' or element == 'p_' or element == 'link_id':
        element = ''
    elif element in ['fenced', 'indented']:
        if element == 'indented':
            i = len(content) - 1
            while i > 0:
                if content[i] != '\n':
                    break
                i -= 1
            content = content[:i+1]
        lg = f' class="language-{html.unescape(params[2].replace('\\', ''))}"' if element == 'fenced' and params[2] else ''
        if content:
            content.append('\n')
        content.insert(0, f'<pre><code{lg}>')
        if last != '\n':
            content.insert(0, '\n')
        content.append(f'</code></pre>')
        content.append('\n')
    elif element in ['a', 'img']:
        text = content[0]['square']
        url = content[0].get("url")
        link_id = content[0].get("link_id")
        title = content[0].get("title", '').translate(HE_TR)
        title_attr = f' title="{title}"' if title else ''
        if element == 'a':
            ht = f'<{element} href="{url}"{title_attr}>{text}</{element}>'
        else:
            ht = f'<{element} src="{url}" alt="{text}"{title_attr} />'
        content = [ht]
    elif element in ['ol']:
        ol_start = '' if params[1] == 1 else f' start="{params[1]}"'
        content.insert(0, f'<{element}{ol_start}>')
        if last != '\n':
            content.insert(0, '\n')
        content.append(f'\n</{element}>')
    elif element in ['hr']:
        content.insert(0, f'<{element} />')
        if last != '\n':
            content.insert(0, '\n')
    elif element in ['br']:
        content[-1] = f'<{element} />'
    #elif element in ['html']:
    #    content.insert(0, '\n')
    #    if content[-1] != '\n':
    #        content.append('\n')
    elif element in ['html', 'raw']:
        pass
    else:
        content.insert(0, f'<{element}>')
        if last != '\n' and element[0] in ['b', 'u', 'l', 'p', 'h']:
            content.insert(0, '\n')
        if content[-1] != '\n' and element[0] in ['b', 'u']:
            content.append('\n')
        content.append(f'</{element}>')
        if element[0] in ['u', 'p', 'b']:
            content.append('\n')
    return content


def forward_cursor(md, start, offset):
    """Skip spaces and tabs."""
    i = start
    nb = 0
    while i < start + offset:
        if md[i] == ' ':
            nb += 1
        elif md[i] == '\t':
            nb += 4
        if nb >= offset:
            break
        i += 1
    return i


def context(md: str, start: int, stop: int, stack, links, close = False) -> int:
    """Adjust context by exiting blocks if necessary."""
    broken = False
    i = start
    tok, sp_or_tabs, w = i, False, 0
    node_cursor = 1
    p_ending = False
    if len(stack) == 1:
        return i

    hr, eol = check_hr(md, i)
    setext, eol = check_setext(md, i)

    if hr:
        close = True

    if setext and stack[-1][0] in ['p', 'p_', 'span'] and stack[-2][0] not in ['blockquote', 'li']:
        elt = 'h1' if setext == '=' else 'h2'
        if stack[-1][1][-1] == '<br />':
            stack[-1][1].pop()
        content = stack[-1][1] if stack[-1][1][-1] not in '\t' else stack[-1][1][:-1]
        cp = stack[-1][2]
        if stack[-1][0] == 'span':
            stack.pop()
        stack[-1] = (elt, content, cp, None)
        return eol

    while i < stop + 1 and not close:
        node, _, _, params = stack[node_cursor]
        i0 = i
        tok, ii, sp_or_tabs, w = indentation(md, i0)
        tok2, i, seq, w2 = prefix(md, ii)
        dprint(f'        | {node} sptabs={sp_or_tabs} w={w} seq=@{seq}@ i0={i0} ii={ii} i={i}')

        if node in ['link_id']:
            link_id, url, title = params
            if url is None:
                _, url, title, eoli = check_link_def(md, i, stop, search="URL")
                if url:
                    params[1] = url
                    params[2] = title
                    return eoli
                else:
                    stack[-1] = ('p', [md[stack[-1][2]:i-1]], stack[-1][2], False)
                    broken = True
            elif not title:
                _, _, title, eoli = check_link_def(md, i, stop, search="TITLE")
                if title:
                    params[2] = title
                    i = eoli
                broken = True
            else:
                broken = True
        elif node in ['em', 'strong', 'code']:
            return i0
        elif node in ['p', 'p_']:
            if hr or (seq == '#' and w < 4) or (seq == '`' and w2 >= 3):
                broken = True
                i = i0
            elif md[ii] in '\r\n':
                p_ending = True
                broken = True
                i = i0
            elif md[i] == '<' and (typ := check_html_block(md, i, stop)):
                if typ[0] < 7:
                    broken = True
                    i = i0
                else:
                    node_cursor += 1
                    i -= 1
            elif md[i] in '-.' and md[i+1] in ' \t':
                broken = True
                if len(stack) > 2 and stack[-3][0] in ['ul', 'ol']:
                    #i = start + stack[-3][3][0]
                    i = ii
                else:
                    i = i0
            else:
                node_cursor += 1
                #i -= 1
                i = i0 - 1
        elif node == 'li':
            offset, _ = stack[node_cursor-1][3]
            dprint(f'        | li with offset {offset}', node_cursor)
            if md[i] in '+-*' or (seq == 'digits' and md[i] == '.'):
                _, _, _, w = indentation(md, start)
                #if i-start < offset:
                if w < offset:
                    broken = True
                    i = ii
                else:
                    node_cursor += 1
                    i -= 1
            elif stack[-1][0][0] != 'p' and md[ii] not in ' \r\n' and w>=offset:
                node_cursor += 1
                i = forward_cursor(md, i0, offset)
                dprint(f'        | forward to {i}')
            elif stack[-1][0][0] != 'p' and md[ii] not in ' \r\n' and w<offset:
                node_cursor -= 1
                broken = True
                i = i0
            else:
                node_cursor += 1
                i -= 1
        elif node in ['ul', 'ol']:
            if seq == '#':
                i = ii
                broken = True
            else:
                node_cursor += 1
                i = i0 - 1
        elif node == 'blockquote':
            if md[i] == '>':
                node_cursor += 1
                if md[i+1] == ' ':
                    i += 1
            elif node_cursor == len(stack) - 2 and md[ii] not in '\n':
                node_cursor += 1
                i -= 1
            else:
                broken = True
        elif node == 'fenced':
            if w < 4 and params[0] == seq and params[1] <= w2 and not md[i:stop].lstrip(' '):
                broken = True
                i = stop
            else:
                if w >= params[3]:
                    o = params[3]
                else:
                    o = w
                i = i0 - 1 + o
                node_cursor += 1
        elif node in ['hr']:
            i = i0 - 1
            broken = True
        elif node[0] == 'h' and len(node) == 2:
            i = i0
            broken = True
        elif node == 'html':
            if params >= 6:
                if md[ii] in '\r\n':
                    broken = True
                else:
                    node_cursor += 1
                    i = i0-1
            elif params == 1:
                if md[ii] == '\n':
                    stack[-1][1].append('\n')
                line = md[i:stop].lower()
                for t in TAGS_CONDITION_1:
                    if t in line and '</' + t + '>' in line:
                        stack[-1][1].append('\n')
                        stack[-1][1].append(md[i:stop])
                        i = stop
                        broken = True
                        break
                if not broken:
                    node_cursor += 1
                    i = i0-1
            elif params > 1 and params < 6:
                if md[ii] == '\n':
                    stack[-1][1].append('\n')
                line = md[i:stop].lower()
                ending = {2: '-->', 3: '?>', 4: '>', 5: ']]>'}
                if ending[params] in line:
                    stack[-1][1].append('\n' + md[i0:stop])
                    i = stop
                    broken = True
                    break
                else:
                    node_cursor += 1
                    i = i0-1
        elif node == 'indented':
            if  w<4 and md[i] != '\n':
                broken = True
            else:
                node_cursor += 1
                i = i0 + 4 - 1
        if broken:
            break
        elif node_cursor >= len(stack):
            return i+1
        i += 1

    if close:
        node_cursor = 1
    nb_exited = len(stack) - node_cursor
    for _ in range(nb_exited):
        if stack[-1][0] == 'link_id':
            link_id, url, title = stack[-1][3]
            if link_id and url is not None and link_id.upper() not in links:
                links[link_id.upper()] = (quote(url.replace('\\', ''), safe=":/?=&*()"), title.replace('\\', ''))
        if stack[-1][0] == 'p_' and p_ending:
            stack[-1] = ('p', stack[-1][1], stack[-1][2], True)
        if stack[-1][0] == 'li' and stack[-1][3] == 1 and len(stack[-1][1]) > 1 and stack[-1][1][1] == '<p>':
            stack[-1][1][0] = ''
            stack[-1][1][1] = ''
            stack[-1][1][-2] = ''
            stack[-1][1][-1] = ''
        if stack[-1][0] == 'p':
            if stack[-1][1][-1] == '<br />':
                stack[-1][1][-1] = ''
        element, fragments, rb, params = stack.pop()
        if element in ['em', 'strong', 'code', 'span']:
            dprint(f'        | {element} should be rolled back to rb={rb} params={params}')
            offset = 0
            if element == 'code':
                offset = params
            return rb
        else:
            current = stack[-1][1]
            last = current[-1] if current else ''
            current += html_text(element, fragments, params, last)
    return i


def structure(md: str, start: int, stop: int, stack, links) -> list:
    """Build new blocks.

    ...
    """
    i = start
    sp_or_tabs, w1 = False, 0
    seq, w2 = '', 0
    phase = ''
    if stack[-1][0] == 'fenced':
        return i
    hr, eol = check_hr(md, i)
    if hr:
        stack.append(('hr', [], i, None))
        return eol
    if stack[-1][0] in ['html', 'link_id']:
        return i

    while i < stop + 1:
        node, accu, _, _ = stack[-1]
        i0 = i
        extra = 2 if i0 > 0 and md[i0-1] == '\t' else 0
        _, ii, sp_or_tabs, w = indentation(md, i0, extra)
        _, i, seq, w2 = prefix(md, ii)
        dprint(f'        | {node} i0={i0} sptabs={sp_or_tabs} w={w} w2={w2} ii={ii} seq=@{seq}@  i={i}')

        if i <= stop and w<4 and stack[-1][0] != 'p':
            link_id, url, title, eoli = check_link_def(md, i, stop)
            if link_id:
                stack.append(('link_id', [], i, [link_id, url, title]))
                return stop
        if seq in '`~' and w < 4 and w2 >= 3 and (i >= stop or seq == '~' or '`' not in md[i:stop]):
            if stack[-1][0] == 'li':
                nb = stack[-1][3] + 1 if stack[-1][3] else 1
                stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
            lang = md[i:stop].lstrip(' ').split(" ", 1)[0]
            stack.append(('fenced', [], i, (seq, w2, lang, w)))
            i = stop
            return i
        elif md[i] in '\r\n' and seq not in '#`':
            return i
        elif stack[-1][0] in ['fenced', 'indented']:
            i = i0
            return i
        elif sp_or_tabs and w >= 4 and stack[-1][0] not in ['p', 'p_']:
            if stack[-1][0] == 'blockquote':
                extra = 2 if i0 > 0 and md[i0+1] == '\t' else 0
                _, ii, sp_or_tabs, w = indentation(md, i0+1, extra)
            add_spaces = w - 4
            if stack[-1][0] == 'li':
                nb = stack[-1][3] + 1 if stack[-1][3] else 1
                stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
            stack.append(('indented', [], i, add_spaces))
            return ii
        elif seq  == '#' and md[i] in ' \t\n' and w < 4 and w2 <= 6:
            stack.append((f'h{w2}', [], i, None))
            return i+1
        elif md[i] == '>':
            if stack[-1][0] == 'li':
                nb = stack[-1][3] + 1 if stack[-1][3] else 1
                stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
            stack.append(('blockquote', [], i, None))
        elif md[i] in '+-*' and i+1<len(md) and md[i+1] in ' \t':
#            if stack[-1][0] == 'li':
#                nb = stack[-1][3] + 1 if stack[-1][3] else 1
#                stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
            if stack[-1][0] != 'ul':
                if stack[-1][0] == 'li':
                    nb = stack[-1][3] + 1 if stack[-1][3] else 1
                    stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
                if len(stack) >= 2 and stack[-2][0] == 'ul':
                    offset = stack[-2][3][0]
                else:
                    offset = 0
                _, ix, _, _ = indentation(md, i+1)
                stack.append(('ul', [], i, (offset+ix-i0, None)))
            stack.append(('li', [], i, 0))
            i += 1
        elif seq == 'digits' and md[i] in '.)' and i+1<len(md) and md[i+1] in ' \t' and int(md[i0:i]) < 1000000000:
            if stack[-1][0] != 'ol':
                if len(stack) >= 2 and stack[-2][0] == 'ol':
                    offset = stack[-2][3][0]
                else:
                    offset = 0
                _, ix, _, _ = indentation(md, i+1)
                stack.append(('ol', [], i, (offset+ix-i0, int(md[i0:i]))))
            stack.append(('li', [], i, 0))
            i += 1
        elif md[ii] == '<' and stack[-1][0] != 'html' and (typ := check_html_block(md, ii, stop)):
            dprint('        | html block', typ)
            condition, ends = typ
            if ends:
                current = stack[-1][1]
                current += md[i0:stop]
            else:
                stack.append(('html', [md[i0:stop]], i, condition))
            return stop
        elif md[ii] not in '\r\n' and stack[-1][0] in ('root', 'blockquote', 'li'):
            nb = stack[-1][3] + 1 if stack[-1][3] else 1
            if stack[-1][0] == 'li' and stack[-1][3] == 0:
                stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
                stack.append(('p_', [], ii, False))
            elif stack[-1][0] == 'li' and stack[-1][3] == 1:
                stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
                stack.append(('p', [], ii, False))
            else:
                stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], nb)
                stack.append(('p', [], ii, False))
            return ii
        else:
            return ii

        i += 1
    return i


def open_element(md, tok, i, stack, offset, element, params, init = None):
    """Flush segment and add new span element."""
    stack[-1][1].append(md[tok:i-offset+1])
    init = [] if init == None else init
    stack.append((element, init, i-offset+1, params))
    tok = i + 1
    return tok


def close_element(md, tok, i, stack, offset):
    """Flush segment and close current element."""
    b, e = tok, i
    if stack[-1][0] == 'code' and i-tok>2 and md[tok] == ' ' and md[i-offset] == ' ':
        b, e = tok+1, i-1
    stack[-1][1].append(md[b:e-offset+1])
    prev = stack.pop()
    current = stack[-1][1]
    last = current[-1] if current else ''
    current += html_text(prev[0], prev[1], prev[3], last)
    tok = i + offset
    return tok


def keep_element(md, tok, i, stack, offset):
    """."""
    #stack[-1][1].append(md[tok:i-offset+1]) TODO archive
    prev = stack.pop()
    current = stack[-1][1]
    current += [prev]
    tok = i + offset
    return tok


def basic_entity_substitution(c):
    """Simple entity substitution for single character."""
    if c in HE:
        return HE[c]
    else:
        return c


def html_entity(md, tok, i, stack):
    """Turn special chars into HTML entities."""
    stack[-1][1].append(md[tok:i])
    stack[-1][1].append(basic_entity_substitution(md[i]))
    tok = i + 1
    return tok


def detect_link(md, start, stop):
    """Dedicated parsing of links."""
    i = start
    res = {}
    tmp = [('tmp', [''], 0)]
    tmp_payload = tmp[0][1]
    url_b = 0
    url_e = 0
    link_b = 0
    title_b = 0
    brackets = ''
    title_m = ''
    search = "SQUARE"
    if i == stop:
        return None, start
    while i < stop:
        if search == "SQUARE":
            if md[i] == '`':
                return None, start
            if md[i] == ']':
                i = payload(md, start, i, tmp)
                j = 0
                while j < len(tmp_payload):
                    if tmp_payload[j]:
                        break
                    j += 1
                content = '' if len(tmp_payload) < 2 else ''.join(tmp_payload[j:])
                if md[i] == '(':
                    res['square'] = content
                    search = "URL"
                elif md[i] == '[':
                    res['square'] = content
                    link_b = i+1
                    search = "LINK"
                else:
                    res['square'] = content
                    #res['link_id'] = content
                    res['link_id'] = md[start:i-1]
                    return res, i
        elif search == "LINK":
            if md[i] == ']':
                if link_b != i:
                    res['link_id'] = md[link_b:i]
                else:
                    res['link_id'] = res['square']
                i += 1
                return res, i
        elif search == "URL":
            if not url_b and md[i] == '<':
                brackets = '>'
            if not url_b and md[i] in ')':
                res['url'] = ''
                search = "TITLE"
            elif not url_b and md[i] not in ' \t':
                url_b = i
            elif brackets and url_b and md[i] in '>':
                url = md[url_b+1:i]
                if '\n' in url:
                    return None, start
                url = quote(url.replace('\\', ''), safe=":/?=&*()")
                res['url'] = url
                i += 1
                search = "TITLE"
            elif not brackets and url_b:
                if md[i] in '"\'(' and md[i-1] not in ' \n':
                    url_e = i
                elif md[i] in ')"\'(':
                    url = md[url_b:url_e+1].replace('\\', '')
                    if ' ' in url:
                        return None, start
                    elif '\n' in url:
                        return None, start
                    url = quote(html.unescape(url), safe=":/?=&*()")
                    res['url'] = url
                    i -= 1
                    search = "TITLE"
                elif md[i] not in ' \t':
                    url_e = i
        elif search == "TITLE":
            if md[i] in ' \t':
                pass
            elif not title_b and md[i] == ')':
                res['title'] = ''
                return res, i+1
            elif not title_b and md[i] in '"\'(':
                title_b = i+1
                title_m = MATCHING[md[i]]
            elif title_b and md[i] == title_m:
                res['title'] = html.unescape(md[title_b:i].replace('\\', ''))
                _, i, _, _ = indentation(md, i+1)
                if md[i] == ')':
                    return res, i+1
                else:
                    return None, start
        i += 1
    if search in ("SQUARE", "URL"):
        return None, i
    return res, i


def check_span(md: str, tok: int, i: int):
    """Validate and identify span type."""
    span = md[tok+1:i]
    if '@' in span:
        return 'automail'
    elif ':' in span:
        if ' ' not in span:
            return 'autolink'
        else:
            return None
    else:
        if check_tag(span, 0, len(span)):
            return 'raw'
        else:
            return None


def is_flank(md: str, pattern: str, i: int, side: str):
    """."""
    inner = i+1 if side == 'LEFT' else i-1-len(pattern)+1
    outer = i-1-len(pattern)+1 if side == 'LEFT' else i+1
    if (
            #(md[i+1] != pattern[0] or side == 'RIGHT') *foo**
            md[i+1] != pattern[0]
            and md[inner] not in SP
            and (not md[inner] in PUNCTUATION or (md[inner] in PUNCTUATION and md[outer] in SEPS))
    ):
        return True
    return False


def is_underscore_del(md: str, pattern: str, i: int, side: str):
    """."""
    opp_side = 'RIGHT' if side == 'LEFT' else 'LEFT'
    inner = is_flank(md, pattern, i, side)
    outer = is_flank(md, pattern, i, opp_side)
    p = i-1-len(pattern)+1 if side == 'LEFT' else i+1
    if (
        md[i+1] != pattern[0]
        and inner
        and (not outer or (outer and md[p] in PUNCTUATION))
    ):
        return True
    return False


def payload(md: str, start: int, stop: int, stack, offset=0) -> list:
    """Process spans in the content."""
    #BACKSLASH_ESCAPED =  '`*_{}[]()#+-.!'
    #if md[start] == '\n':
    #    return stop+1
    i = start
    idx = 0
    tok, seq, w = start, '', 0
    stl = True
    skip = False
    found_bs = False
    prev_i = -2
    bypass = []

    if stack[-1][0] in ['p', 'p_', 'indented', 'em', 'strong'] and offset == 0 and stack[-1][1]:
        stack[-1][1].append('\n')
    elif stack[-1][0] in ['fenced'] and offset == 0 and stack[-1][1]:
        stack[-1][1].append('\n')
    elif stack[-1][0] in ['fenced'] and offset == 0 and not stack[-1][1]:
        stack[-1][1].append('')
    elif stack[-1][0] in ['code'] and md[i] != '`' and stack[-1][1] and offset == 0:
        stack[-1][1].append(' ')

    if offset == 1:
        i += 1
        start += 1

    if stack[-1][0] == 'html':
        stack[-1][1].append('\n')
        stack[-1][1].append(md[start:stop])
        return stop+1

    matches = []
    markers = []
    if stack[-1][0] not in ['fenced', 'indented']:
        matches = regex.finditer(md, start, stop)
    for match in matches:
        markers.append(match.start())

    #if stack[-1][0] == 'fenced':
    #    markers = []
    #else:
    #    j = start
    #    markers = []
    #    while j < stop:
    #        if md[j] in patterns:
    #            markers.append(j)
    #        j += 1
    dprint(f'        | markers={markers}')

    while idx < len(markers):
        i = markers[idx]
        dprint('        | ', i, md[i], tok, stl, stack[-1][0])
        if i < tok:
            idx += 1
            continue
        if i == prev_i+1:
            idx += 1
            continue
        if md[i] == '\\' and md[i+1] in BACKSLASH_ESCAPED and stack[-1][0] not in ['indented', 'code', 'span']:
            c = md[i+1]
            stack[-1][1].append(md[tok:i] + basic_entity_substitution(c))
            tok = i+2
            found_bs = True
            prev_i = i
            idx += 1
            continue
        if md[i] == '&' and stack[-1][0] not in ['indented', 'code', 'span']:
            f = md.find(';', i+2, stop)
            if f > -1 and ' ' not in md[i:f+1]:
                text = md[i:f+1]
                if len(text) > 3 and text[2:-1].isdigit() and int(text[2:-1]) > 1114111:
                    u_text = text
                else:
                    u_text = html.unescape(text)
                if len(u_text) == len(text):
                    stack[-1][1].append(md[tok:i] + basic_entity_substitution('&') + text[1:])
                    tok = f+1
                else:
                    stack[-1][1].append(md[tok:i] + basic_entity_substitution(u_text))
                    tok = f+1
            else:
                stack[-1][1].append(md[tok:i] + basic_entity_substitution(md[i]))
                tok = i+1
            idx += 1
            continue
        if stl and i > 1 and md[i-2:i+1] in ['***','___'] and stack[-2][0] == 'em' and stack[-1][0] == 'strong':
            tok = close_element(md, tok, i, stack, 3)
            tok = close_element(md, tok, i, stack, 3)
            tok -= 2
        elif stl and i > 0 and md[i-1:i+1] == '**' and stack[-1][0] == 'strong' and is_flank(md, '**', i, 'RIGHT'):
            tok = close_element(md, tok, i, stack, 2)
            tok -= 1
        elif stl and i > 0 and md[i-1:i+1] == '__' and stack[-1][0] == 'strong' and is_underscore_del(md, '__', i, 'RIGHT'):
            tok = close_element(md, tok, i, stack, 2)
            tok -= 1
        elif stl and md[i] == '*' and md[i-1] != '*' and stack[-1][0] == 'em' and is_flank(md, md[i], i, 'RIGHT'):
            tok = close_element(md, tok, i, stack, 1)
        elif stl and md[i] in ['_'] and md[i-1] != '_' and stack[-1][0] in ('em') and is_underscore_del(md, md[i], i, 'RIGHT'):
            tok = close_element(md, tok, i, stack, 1)
        elif stl and i > start+1 and md[i-2:i+1] in ['***', '___'] and md[i+1] != md[i] and md[i+1] not in SP:
            tok = open_element(md, tok, i, stack, 3, 'em', None)
            tok = open_element(md, tok, i, stack, 3, 'strong', None)
        elif stl and i > start and md[i-1:i+1] in ['**'] and is_flank(md, '**', i, 'LEFT'):
            tok = open_element(md, tok, i, stack, 2, 'strong', None)
        elif stl and i > start and md[i-1:i+1] in ['__'] and is_underscore_del(md, '__', i, 'LEFT'):
            tok = open_element(md, tok, i, stack, 2, 'strong', None)
        elif stl and md[i] == '*'  and is_flank(md, md[i], i, 'LEFT'):
            tok = open_element(md, tok, i, stack, 1, 'em', None)
        elif stl and md[i] == '_' and md[i-1] != '_' and is_underscore_del(md, md[i], i, 'LEFT'):
            tok = open_element(md, tok, i, stack, 1, 'em', None)
        elif md[i-2:i+1] == '```' and stack[-1][0] == 'code' and stack[-1][3] == 3:
            stl = True
            tok = close_element(md, tok, i, stack, 3)
            tok -= 2
        elif md[i-1:i+1] == '``' and stack[-1][0] == 'code' and stack[-1][3] == 2:
            stl = True
            tok = close_element(md, tok, i, stack, 2)
            tok -= 1
        elif md[i:i+1] == '`' and md[i-1] != md[i] and md[i+1] != md[i] and stack[-1][0] == 'code' and stack[-1][3] == 1:
            stl = True
            tok = close_element(md, tok, i, stack, 1)
        elif i> 1 and md[i-2:i+1] == '```' and md[i+1] != '`' and stack[-1][0] != 'code' and i-2 in markers:
            tok = open_element(md, tok, i, stack, 3, 'code', 3)
            stl = False
        elif i> 0 and md[i-1:i+1] == '``' and md[i+1] != '`' and md[i-2] != '`' and stack[-1][0] != 'code' and i-1 in markers:
            tok = open_element(md, tok, i, stack, 2, 'code', 2)
            stl = False
        elif md[i:i+1] == '`' and md[i+1] != md[i] and md[i-1] != md[i] and stack[-1][0] not in ['code', 'span']:
            tok = open_element(md, tok, i, stack, 1, 'code', 1)
            stl = False
        elif md[i:i+1] == '>' and stack[-1][0] == 'span':
            typ = check_span(md, tok, i)
            if typ == 'raw':
                _, content, cp, params = stack[-1]
                stack[-1] = (typ, content, cp, params)
                tok = close_element(md, tok, i, stack, 0)
                tok += 1
                stl = True
            elif typ == 'autolink':
                txt = md[tok+1:i]
                descr = txt.translate(HE_TR)
                url = quote(txt.translate(HE_TR), safe=":/?=&*")
                stack[-1] = ('a', [{'square': descr, 'url': url}], None, '')
                tok = close_element(md, tok, i, stack, 0)
                tok += 1                
            elif typ == 'automail':
                txt = md[tok+1:i]
                prefix = 'mailto:' if '@' in txt and 'mailto' not in txt.lower() else ''
                url = prefix + txt
                url = url.translate(HE_TR)
                stack[-1] = ('a', [{'square': txt, 'url': url}], None, '')
                tok = close_element(md, tok, i, stack, 0)
                tok += 1                
            else:
                _, _, cp, _ = stack.pop()
                dprint(f'        | span should be rolled back to cp={cp}', stack)
                idx = markers.index(cp)
                bypass.append(idx)
                continue
        elif md[i:i+1] == '<'  and stack[-1][0] != 'code' and idx not in bypass and (md[i+1].isalpha() or md[i+1] == '/'):
            tok = open_element(md, tok, i-1, stack, 0, 'span', None)
            stl = False
        elif stack[-1][0] == 'html':
            break
        elif md[i:i+1] == '[' and not skip:
            i0 = i
            if i > 0 and md[i-1] == '!':
                e = 'img'
                o = -1
            else:
                e = 'a'
                o = 0
            rr, i = detect_link(md, i+1, stop)
            if rr is not None:
                rr['original'] = md[i0+o:i]
                tok = open_element(md, tok, i0+o, stack, 1, e, None, [rr])
                tok = keep_element(md, tok, i-1, stack, 1)
            else:
                i = i0-1
        elif md[i] in '<>&"' and stack[-1][0] not in ['span']:
            tok = html_entity(md, tok, i, stack)
        else:
            skip = False

        idx += 1

    last_elt = stack[-1][0]
    last_content = stack[-1][1]

    s = md[tok:stop].translate(HE_TR)

    if stack[-1][0] == 'indented' and stack[-1][3]:
        s = ' ' * stack[-1][3] + s
        stack[-1] = (stack[-1][0], stack[-1][1], stack[-1][2], None)

    if last_elt[0]  == 'h':
        s = s.lstrip(' ').rstrip(' ')
        t = s.rstrip('#')
        if t and t[-1] == ' ':
            s = s.rstrip('#').rstrip(' ')
        elif not t and not (last_content and last_content[0] and last_content[0][-1] == '#'):
            s = ''

    if s:
        last_content.append(s)

    if last_elt in ['p', 'p_', 'em'] and len(last_content[-1]) > 2 and last_content[-1][-2:] == '  ':
        last_content[-1] = last_content[-1].rstrip(' ')
        stack.append(('br', [''], 0, None))
        close_element(md, 0, 0, stack, 0)
    elif last_elt in ['p', 'p_', 'em'] and len(last_content[-1]) > 1 and last_content[-1][-1] == '\\':
        last_content[-1] = last_content[-1].rstrip('\\')
        stack.append(('br', [''], 0, None))
        close_element(md, 0, 0, stack, 0)
    elif last_elt in ['p', 'p_'] and len(last_content[-1]) > 1 and last_content[-1][-1] == ' ':
        last_content[-1] = last_content[-1].rstrip(' ')
    return stop+1


def dprint(*args, **kwargs):
    """Custom print with a global switch for debug."""
    if "DEBUG" in globals() and DEBUG:
        print(*args, **kwargs)


def transform(md: str, start: int = 0) -> str:
    """Render HTML from markdown string."""
    res = ''
    i = start
    stack = [('root', [], i, None)] #node, accu, checkpoint, optional parameters
    links = {}
    phase = "in_context"
    skip = 0

    while True:
        eol = md.find("\n", i)
        eol = len(md) if eol == -1 else eol
        dprint(f'{i:2} | {eol:2} | {repr(md[i:eol+1])} {phase}')
        
        if phase == "in_context":
            dprint(f'{i:2} | _c | {".".join([x[0] for x in stack[0:]]):25}')
            before = i
            i = context(md, i, eol, stack, links)
            dprint(f'        | after context i={i} => {".".join([x[0] for x in stack[0:]])}')
            phase = "in_structure"
            if i < before:
                dprint(f'        | ROLLBACK i={i} before={before}')
                skip = 1
                phase = "in_payload"
                continue
            else:
                if stack[-1][0] in ['indented', 'fenced']:
                    phase = "in_payload"
                else:
                    phase = "in_structure" if i < eol else "fforward"

        if phase == "in_structure":
            dprint(f'{i:2} | _s | {".".join([x[0] for x in stack[0:]]):25}')
            i = structure(md, i, eol, stack, links)
            dprint(f'        | after structure i={i} => {".".join([x[0] for x in stack[0:]])}')
            phase = "in_payload" if i < eol else "fforward"

        if phase == "in_payload":
            dprint(f'{i:2} | _p | {" ":25}')
            r = eol-1 if eol > 0 and md[eol-1] == '\r' else eol
            payload(md, i, r, stack, skip)
            skip = 0
            dprint(f'        | after payload => {r:2} {stack[-1]}')
            phase = "in_context"

        i = eol+1
        phase = "in_context"

        if i >= len(md):
            dprint(f'{i:2} | ef | eol={eol} {".".join([x[0] for x in stack[0:]]):25} ')
            before = i
            i = context('\n', i, eol, stack, links, close=True)
            if i < before:
                dprint(f'        | ROLLBACK i={i} before={before}')
                skip = 1
                phase = "in_payload"
                continue
            dprint(f'        | => {".".join([x[0] for x in stack[0:]])}')
            break

    all_fragments = stack[0][1]

    if all_fragments and all_fragments[0] == '\n':
        all_fragments = all_fragments[1:]
    if all_fragments and all_fragments[-1] != '\n':
        all_fragments.append('\n')
    dprint('\n', 'fragments', all_fragments)
    dprint(' links', links, '\n')
    
    for j in range(len(all_fragments)-1, -1, -1):
        x = all_fragments[j]
        if type(x) == tuple:
            obj = x[1][0]
            if 'link_id' in obj:
                link_id = obj['link_id']
                obj['url'], obj['title'] = links.get(link_id.upper(), (None, ''))
            all_fragments.pop(j)
            if obj['url'] is not None:
                link = html_text(x[0], x[1], x[3], '')
            else:
                link = [obj['original']]
            all_fragments[j:j] = link

    res = ''.join(all_fragments)
    return res


def main():
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Transform Markdown into HTML")
    parser.add_argument("input", nargs="?", default="-", help="Input file name or - for stdin")
    args = parser.parse_args()
    if args.input == "-":
        f = sys.stdin
    else:
        f = open(args.input, "r", encoding="utf-8")
    print(transform(f.read()))


if __name__ == "__main__":
    main()

              
