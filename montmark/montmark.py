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

import argparse
import re

#DEBUG = True

patterns = ['*', '_', '`', '[', '<', '>', '&']
escaped = [re.escape(pattern) for pattern in patterns]
spans = '|'.join(escaped)
regex = re.compile(spans)


def str_between_spaces_tabs_nls(md: str, start: int, stop: int):
    """Skip spaces, tabs, newlines, and return following sequence."""
    res = ''
    i = start
    while i < stop:
        if not res and md[i] in ' \t\n':
            i += 1
            continue
        if md[i] not in ' \t\n':
            res += md[i]
        else:
            break
        i += 1
    return res, i


def check_link_id(md: str, start = 0):
    """Dedicated detection of out-of-band link definition."""
    url = ''
    title = ''
    i = start
    if md[i] not in ' [':
        return False, False, False, -1
    c = md.find('[', i, i+4)
    if c == -1 or md[i:c] != ' ' * (c - i):
        return False, False, False, -1
    i = c + 1
    c = md.find('\n', i)
    eol = c if c != -1 else len(md)
    c = md.find(']', i, eol)
    if c == -1:
        return False, False, False, -1
    link_id = md[i:c]
    i = c + 1
    if md[i] != ':':
        return False, False, False, -1
    i += 1
    if md[i] not in ' \t\n':
        return False, False, False, -1
    c = md.find('\n', i)
    c = md.find('\n', c+1)
    eol = c if c != -1 else len(md)
    url, i = str_between_spaces_tabs_nls(md, i, eol)
    if url and url[0] == '<' and url[-1] == '>':
        url = url[1:-1]
    c = md.find('\n', i)
    c = md.find('\n', c+1)
    eol = c if c != -1 else len(md)
    title, i = str_between_spaces_tabs_nls(md, i, eol)
    c = md.find('\n', i)
    eol = c if c != -1 else len(md)
    if title and title[0] in '"(' and title[-1] in '")':
        title = title[1:-1]
    elif title:
        return False, False, False, -1
    else:
        pass
    return (link_id, url, title, eol)


def check_setext(md: str, start = 0):
    """Dedicated detection of setext headers."""
    tok = ''
    nb = 0
    i = start
    c = md.find('\n', i)
    eol = c if c != -1 else len(md)
    while i < eol:
        if not tok:
            if md[i] in '=-':
                tok = md[i]
                nb = 1
            else:
                return False, -1
            i += 1
            continue
        if md[i] != tok:
            return False, -1
        elif md[i] == tok:
            #toks += md[i]
            nb += 1
        i += 1
    res = tok if nb >= 2 else False
    return res, eol


def check_hr(md: str, start = 0):
    """Dedicated detection of horizontal rule."""
    toks = ''
    i = start
    c = md.find('\n', i)
    eol = c if c != -1 else len(md)
    while i < eol:
        if not toks:
            if md[i] in '*_-':
                toks = md[i]
            elif md[i] == ' ':
                pass
            else:
                return False, -1
            i += 1
            continue
        if md[i] != ' ' and md[i] != toks[0]:
            return False, -1
        elif md[i] in toks:
            toks += md[i]
        elif md[i] == ' ':
            pass
        i += 1
    res = True if len(toks) >= 3 else False
    #c = md.find('\n', i)
    #eol = c if c != -1 else len(md)
    return res, eol


def indentation(md: str, start: int = 0) -> tuple:
    """Find & expand spaces and tabs."""
    i = start
    found, w = False, 0
    while i < len(md):
        found = True if not found and md[i] in ' \t' else found
        if md[i] == ' ':
            w += 1
        elif md[i] == '\t':
            w += 4
        else:
            return start, i, found, w
        i += 1


def prefix(md: str, start: int = 0) -> tuple:
    """Isolate digits at start."""
    i = start
    seq, w = '', 0
    while i < len(md):
        if not seq and md[i] in '#`':
            seq = md[i]
        elif not seq and md[i] in '1234567890':
            seq = 'digits'
        if seq == 'digits' and md[i] in '1234567890':
            w += 1
        elif seq == '#' and md[i] == '#':
            w += 1
        elif seq == '`' and md[i] == '`':
            w += 1
        else:
            return start, i, seq, w
        i += 1


def html_text(element: str, content):
    """Prepare html segments but keep them in a list for future join."""
    isBlock = '\n' if element[0] in ['p', 'h', 'b', 'u', 'o', 'l'] else ''
    isList = '\n' if element[0] in ['u', 'o'] else ''
    if element in ['fenced', 'indented']:
        content.insert(0, f'<pre><code>')
        content.append(f'</code></pre>\n')
    elif element in ['em&strong']:
        content.insert(0, f'<{element}>{isList}')
        content.append(f'</{element}>{isBlock}')
    elif element in ['a', 'img']:
        title = f' title="{content["title"]}"' if 'title' in content else ''
        obj = content[0]["obj"]
        url = content[0].get("url")
        title = content[0].get("title")
        obj.insert(0, f'<{element} href="')
        obj.insert(1, f'{url}')
        obj.insert(2, f'" title="')
        obj.insert(3, f'{title}')
        obj.insert(4, f'">')
        obj.append(f'</{element}>')
        content = obj
    elif element in ['hr']:
        content.insert(0, f'\n<{element} />')
    elif element in ['html']:
        pass
    else:
        content.insert(0, f'<{element}>{isList}')
        content.append(f'</{element}>{isBlock}')
    return content

        
def context(md: str, start: int, stop: int, stack) -> int:
    """Adjust context by exiting blocks if necessary."""
    broken = False
    i = start
    tok, sp_or_tabs, w = i, False, 0
    node_cursor = 1
    if len(stack) == 1:
        return i

    setext, eol = check_setext(md, i)
    if setext:
        if stack[-1][0] == 'p':
            elt = 'h1' if setext == '=' else 'h2'
            stack[-1] = (elt, stack[-1][1][:-1], stack[-1][2])
        return eol

    hr, eol = check_hr(md, i)
    if hr:
        return eol
    
    while i < len(md) and not hr:
        node = stack[node_cursor][0]

        i0 = i
        tok, i, sp_or_tabs, w = indentation(md, i)
        tok2, i, seq2, w2 = prefix(md, i)
        
        if node in ['p']:
            if md[i] in '\r\n' or seq2 == '#' or (sp_or_tabs and md[i] != ' ' and i-tok >= 4):
                broken = True
                i = i0
            else:
                return i
        elif node in ['ul', 'ol', 'li']:
            if md[i] in '\r\n':
                broken = True
            elif sp_or_tabs and w >= 4 and (md[i] in '+-*' or (seq2 == 'digits' and md[i] == '.')):
                nested = (i-tok) // 4
                current = sum([1 for x in stack if x[0] in['ul', 'ol', 'li']]) // 2
                if nested >= current:
                    node_cursor += 2 
                else:
                    node_cursor += ((current - nested) * 2 + 1)
                    broken = True
            elif md[i] in '+-*':
                node_cursor += 1
                broken = True
            elif seq2 == 'digits' and md[i] == '.':
                i = tok2
                node_cursor += 1
                broken = True
        elif node == 'blockquote':
            if md[i] == '>':
                node_cursor += 1
                i += 1
            else:
                i = i0
                broken = True
            #if md[i] in '\r\n':
            #    broken = True
            #else:
            #    node_cursor += 2
        elif node == 'fenced':
            if seq2 == '`' and w2 == 3:
                broken = True
                i = stop
            else:
                i = i0
                node_cursor += 1
        elif node[0] == 'h' and len(node) == 2:
            broken = True
            i = start
        elif node == 'html':
            if md[i] in '\r\n':
                broken = True
            else:
                node_cursor += 1
        elif node == 'indented':
            broken = True
        elif node in ['hr']:
            broken = True

        if broken:
            break
        elif node_cursor >= len(stack):
            return i
        i += 1
        
    x = len(stack) - node_cursor
    for _ in range(len(stack) - node_cursor):
        element, fragments, _ = stack.pop()
        current = stack[-1][1]
        if element == 'p':
            fragments.pop(-1)
        current += html_text(element, fragments)
    return i


def structure(md: str, start: int, stop: int, stack) -> list:
    """Build new blocks."""
    i = start
    sp_or_tabs, w1 = False, 0
    seq2, w2 = '', 0
    phase = ''
    if stack[-1][0] == 'fenced':
        return i
    hr, eol = check_hr(md, i)
    if hr:
        stack.append(('hr', [], i))
        return eol
    while i < len(md):
        node, accu, _ = stack[-1]

        i0 = i
        _, i, sp_or_tabs, w1 = indentation(md, i)
        _, i, seq2, w2 = prefix(md, i)

        if seq2  == '`' and w2 == 3:
            stack.append(('fenced', [], i))
            i = stop
            return i
        elif md[i] in '\r\n':
            return i
        elif stack[-1][0] == 'fenced':
            i = i0
            return i
        elif sp_or_tabs and w1 >= 4:
            stack.append(('indented', [], i))
            return i
        elif seq2  == '#' and md[i] == ' ' and w2 <= 6:
            stack.append((f'h{w2}', [], i))
        elif md[i] == '>':
            stack.append(('blockquote', [], i))
        elif md[i] in '+-*':
            if stack[-1][0] != 'ul':
                stack.append(('ul', [], i))
            stack.append(('li', [], i))
        elif seq2 == 'digits' and md[i] == '.':
            if stack[-1][0] != 'ol':
                stack.append(('ol', [], i))
            stack.append(('li', [], i))
        elif md[i] == '<' and not sp_or_tabs and stack[-1][0] != 'html':
            stack.append(('html', [], i))
            return i
        elif md[i] not in '\r\n' and stack[-1][0] in ('root', 'blockquote'):
            if md[i] == '\\':
                i += 1
            stack.append(('p', [], i))
            return i
        else:
            return i

        i += 1
    return i


#def payload_other(md: str, start: int, stop: int, stack) -> list:
#    """Process spans in the content."""
#
#    patterns = ['*', '_', '`', '[']
#
#    if md[start] == '\n':
#        return start+1
#    i = start
#    tok, seq, w = i, '', 0
#    matches = regex.finditer(md, i, stop)
#    while i < stop:
#
#        if md[i] not in patterns:
#            continue
#        
#        TODO
#
#        i += 1
#
#    stack[-1][1].append(md[tok:stop])
#    return stop+1


def open_element(md, tok, i, stack, offset, element):
    """Flush segment and add new span element."""
    stack[-1][1].append(md[tok:i-offset+1])
    stack.append((element, [], i-offset+1))
    tok = i + 1
    return tok


def close_element(md, tok, i, stack, offset):
    """Flush segment and close current element."""
    stack[-1][1].append(md[tok:i-offset+1])
    prev = stack.pop()
    current = stack[-1][1]
    if prev[0] != 'span':
        current += html_text(prev[0], prev[1])
    else:
        current += prev[1]
    tok = i + offset
    return tok


def html_entity(md, tok, i, stack):
    """Turn special chars into HTML entities."""
    stack[-1][1].append(md[tok:i])
    HE = {'<': '&lt;', '>': '&gt;', '&': '&amp;'}
    stack[-1][1].append(HE[md[i]])
    tok = i + 1
    return tok


def detect_link(md, i, stop):
    """Dedicated parsing of links."""
    res = {}
    tmp = [('tmp', [''], 0)]
    eob = md.find(']', i, stop)
    i = payload(md, i, eob, tmp, None)
    res['obj'] = tmp[0][1]
    if md[i] == '(':
        eop = md.find(')', i+1, stop)
        boq = md.find('"', i+1, eop)
        u = eop if boq == -1 else boq-1
        res['url'] = md[i+1:u]
        res['title'] = md[u+2:eop-1]
        i = eop + 1
    elif md[i] == '[':
        eob = md.find(']', i+1, stop)
        link_id = md[i+1:eob]
        if link_id:
            res['link_id'] = link_id
        else:
            res['link_id'] = res['obj'][1]
        i = eob + 1
    return res, i


def payload(md: str, start: int, stop: int, stack, refs) -> list:
    """Process spans in the content."""
    if md[start] == '\n':
        return stop+1
    i = start
    tok, seq, w = i, '', 0
    stl = True
    skip = False

    if stack[-1][0] == 'html':
        stack[-1][1].append(md[start:stop])
        stack[-1][1].append('\n')
        return stop+1
    
    if stack[-1][0] == 'fenced':
        matches = []
    else:
        matches = regex.finditer(md, start, stop)

    for match in matches:
        i = match.start()
        if i > 0 and md[i-1] == '\\':
            stack[-1][1].append(md[tok:i-1])
            tok = i
            continue
        #if stack[-1][0] == 'fenced':
        #    break
        if stl and i > 1 and md[i-2:i+1] in ['***','___'] and stack[-2][0] == ('em') and stack[-1][0] == ('strong'):
            tok = close_element(md, tok, i, stack, 3)
            tok -= 2
        elif stl and i > 0 and md[i-1:i+1] in ['**','__'] and md[i+1] != md[i] and stack[-1][0] in ('strong', 'em'):
            tok = close_element(md, tok, i, stack, 2)
            tok -= 1
        elif stl and md[i] in ['*', '_'] and md[i+1] != md[i] and stack[-1][0] in ('em', 'strong'):
            if stack[-1][0] == 'strong' and stack[-2][0] == 'em':
                stack[-2] = 'strong', stack[-2][1], stack[-2][2]
                stack[-1] = 'em', stack[-1][1], stack[-1][2]
            tok = close_element(md, tok, i, stack, 1)
        elif md[i:i+1] == '`' and stack[-1][0] == 'code':
            stl = True
            tok = close_element(md, tok, i, stack, 1)
        elif stl and i > 1 and md[i-2:i+1] in ['***', '___'] and md[i+1] != md[i]:
            tok = open_element(md, tok, i, stack, 3, 'em')
            tok = open_element(md, tok, i, stack, 3, 'strong')
        elif stl and i > 0 and md[i-1:i+1] in ['**', '__'] and md[i+1] != md[i]:
            tok = open_element(md, tok, i, stack, 2, 'strong')
        elif stl and md[i] in ['*', '_'] and md[i+1] != md[i]:
            tok = open_element(md, tok, i, stack, 1, 'em')
        elif md[i:i+1] == '`':
            tok = open_element(md, tok, i, stack, 1, 'code')
            stl = False
        elif md[i:i+1] == '>' and stack[-1][0] == 'span':
            tok = close_element(md, tok, i, stack, 0)
            tok += 1
        elif md[i:i+1] == '<':
            tok = open_element(md, tok, i-1, stack, 0, 'span')
        elif stack[-1][0] == 'html':
            break
        elif md[i:i+1] == '[' and not skip:
            if i > 0 and md[i-1] == '!':
                stack[-1][1].append(md[tok:i-1])
                rr, i = detect_link(md, i+1, stop)
                stack.append(('img', [rr], i))
            else:
                stack[-1][1].append(md[tok:i])
                rr, i = detect_link(md, i+1, stop)
                stack.append(('a', [rr], i))
            if 'link_id' in rr:
                skip = True
                x = 0
                for _, accu, _ in stack:
                    x += len(accu)
                refs.append((rr['link_id'], x+1))
            tok = close_element(md, tok, i, stack, 1)
        elif md[i:i+1] in '<>&':
            tok = html_entity(md, tok, i, stack)
        else:
            skip = False

    if stack[-1][0][0]  == 'h':
        stack[-1][1].append(md[tok:stop].rstrip(' ').rstrip('#'))
    else:
        stack[-1][1].append(md[tok:stop])
    for el, _, _ in stack:
        if el in ['p', 'fenced']:
            stack[-1][1].append('\n')
    return stop+1


def dprint(*args, **kwargs):
    """Custom print with a global switch for debug."""
    if "DEBUG" in globals() and DEBUG:
        print(*args, **kwargs)


def transform(md: str, start: int = 0) -> str:
    """Render HTML from markdown string."""
    res = ''
    i = start
    stack = [('root', [], i)] #node, accu, checkpoints
    refs = []
    links = {}
    while i < len(md):
        #print(stack)
        eol = md.find("\n", i)
        eol = len(md) if eol == -1 else eol
        dprint(f'{i:2} | {eol:2} | {repr(md[i:eol+1])}')
        
        phase = "in_context"
        dprint(f'{i:2} | _c | {".".join([x[0] for x in stack[0:]]):25} ', end="")
        i = context(md, i, eol, stack)
        dprint(f'=> {i:2} | {".".join([x[0] for x in stack[0:]])}')
        phase = "in_structure" if i < eol else "fforward"

        if phase == "in_structure":
            dprint(f'{i:2} | _s | {".".join([x[0] for x in stack[0:]]):25} ', end="")
            link_id, url, title, _ = check_link_id(md, i)
            if link_id:
                links[link_id.upper()] = (url, title)
                i = eol
                continue
            i = structure(md, i, eol, stack)
            dprint(f'=> {i:2} | {".".join([x[0] for x in stack[0:]])}')
            phase = "in_payload" if i < eol else "fforward"

        if phase == "in_payload":
            dprint(f'{i:2} | _p | {" ":25} ', end="")
            r = eol-1 if eol > 0 and md[eol-1] == '\r' else eol
            payload(md, i, r, stack, refs)
            dprint(f'=> {r:2} |')

        i = eol+1
            
    _ = context('\n', 0, 0, stack)
    all_fragments = stack[0][1]
    dprint('\n')
    dprint('fragments', all_fragments, '\n')
    dprint('refs', refs)
    dprint('links', links)
    for a, j in refs:
        link_id = a
        l = links.get(link_id.upper(), ('', ''))
        all_fragments[j] = l[0]
        all_fragments[j+2] = l[1]
    res = ''.join(all_fragments)
    return res


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("file")
    args = parser.parse_args()
    with open(args.file, encoding="utf-8") as f:
        print(transform(f.read()))


if __name__ == "__main__":
    main()

              
