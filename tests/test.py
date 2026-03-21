import unittest
import montmark

tests = [

###
'inline html'
,
'''
a

<table>
    <tr>
        <td>foo</td>
    </tr>
</table>

b
'''
,
'''
<p>a</p>
<table>
<tr>
<td>foo</td>
</tr>
</table>
<p>b</p>
'''
,
###
'html span in p'
,
'a <span>s</span> b','<p>a <span>s</span> b</p>'
,
###
'escaping ampersand'
,
'a b&c d','<p>a b&amp;c d</p>'
,
###
'escaping left angle'
,
'a < b','<p>a &lt; b</p>'
,
###
'simplest paragraph'
,
'p1','<p>p1</p>'
,
###
'multi lines paragraph'
,
'''
p1 a
p1 b
'''
,
'''
<p>p1 a
p1 b</p>
'''
,
###
'separated paragraphs'
,
'''
p1

p2
'''
,
'''
<p>p1</p>
<p>p2</p>
'''
,
###
'blank line made of spaces'
,
'''
p1
  
p2
'''
,
'''
<p>p1</p>
<p>p2</p>
'''
,
###
'2 spaces at eol inserts br'
,
'''
p1a.  
p1b
'''
,
'''
<p>p1a.<br />
p1b</p>
'''
,
###
'atx h1'
,
'# t1','<h1>t1</h1>'
,
###
'atx h2'
,
'## t2','<h2>t2</h2>'
,
###
'atx h3'
,
'### t3','<h3>t3</h3>'
,
###
'atx h4'
,
'#### t4','<h4>t4</h4>'
,
###
'atx h5'
,
'##### t5','<h5>t5</h5>'
,
###
'atx h6'
,
'###### t6','<h6>t6</h6>'
,
###
'atx with closing hashes'
,
'## t2 ##','<h2>t2</h2>'
,
###
'bad atx too many hashes'
,
'####### t7','<p>####### t7</p>'
,
###
'setext h1'
,
'''
t1
==
'''
,
'''
<h1>t1</h1>
'''
,
###
'setext h2'
,
'''
t2
--
'''
,
'''
<h2>t2</h2>
'''
,
###
'p just after atx header'
,
'''
## t1
a b c
'''
,
'''
<h2>t1</h2>
<p>a b c</p>
'''
,
###
'p just after setext header'
,
'''
t1
==
a b c
'''
,
'''
<h1>t1</h1>
<p>a b c</p>
'''
,
###
'simplest blockquote'
,
'''
> p1
'''
,
'''
<blockquote>
<p>p1</p>
</blockquote>
'''
,
###
'multi line blockquote'
,
'''
> p1 a
> p1 b
'''
,
'''
<blockquote>
<p>p1 a
p1 b</p>
</blockquote>
'''
,
###
'lazy blockquote'
,
'''
> p1 a
p1 b
'''
,
'''
<blockquote>
<p>p1 a
p1 b</p>
</blockquote>
'''
,
###
'nested blockquote'
,
'''
> p1
>
>> p2
>
> p3
'''
,
'''
<blockquote>
<p>p1</p>
<blockquote>
<p>p2</p>
</blockquote>
<p>p3</p>
</blockquote>
'''
,
###
'other block in blockquote'
,
'''
> # t1
>
> p1
'''
,
'''
<blockquote>
<h1>t1</h1>
<p>p1</p>
</blockquote>
'''
,
###
'consecutive blockquotes'
,
'''
> b1

> b2
'''
,
'''
<blockquote>
<p>b1</p>
</blockquote>
<blockquote>
<p>b2</p>
</blockquote>
'''
,
###
'unordered asterisks list'
,
'''
* l1
* l2
'''
,
'''
<ul>
<li>l1</li>
<li>l2</li>
</ul>
'''
,
###
'unordered pluses list'
,
'''
+ l1
+ l2
'''
,
'''
<ul>
<li>l1</li>
<li>l2</li>
</ul>
'''
,
###
'unordered hyphen-minus list'
,
'''
- l1
- l2
'''
,
'''
<ul>
<li>l1</li>
<li>l2</li>
</ul>
'''
,
###
'simple ordered list'
,
'''
1. l1
2. l2
'''
,
'''
<ol>
<li>l1</li>
<li>l2</li>
</ol>
'''
,
###
'nested list 2-indent'
,
'''
- i1
  - i1.1
- i2
'''
,
'''
<ul>
<li>i1
<ul>
<li>i1.1</li>
</ul>
</li>
<li>i2</li>
</ul>
'''
,
###
'nested list 4-indent'
,
'''
- i1
    - i1.1
- i2
'''
,
'''
<ul>
<li>i1
<ul>
<li>i1.1</li>
</ul>
</li>
<li>i2</li>
</ul>
'''
,
###
'list item continuation'
,
'''
- i1
a b c
- i2
'''
,
'''
<ul>
<li>i1
a b c</li>
<li>i2</li>
</ul>
'''
,
###
'2 p in list item'
,
'''
- p1

  p2

a
'''
,
'''
<ul>
<li>
<p>p1</p>
<p>p2</p>
</li>
</ul>
<p>a</p>
'''
,
###
'header after list'
,
'''
- i1

# t1
'''
,
'''
<ul>
<li>i1</li>
</ul>
<h1>t1</h1>
'''
,
###
'code block'
,
'''
p1

    c1
'''
,
'''
<p>p1</p>
<pre><code>c1
</code></pre>
'''
,
###
'horizontal rule'
,
'''
p1

* * *

p2
'''
,
'''
<p>p1</p>
<hr />
<p>p2</p>
'''
,
###
'simple inline link inside p'
,
'''
p1a [text](url) p1b
'''
,
'''
<p>p1a <a href="url">text</a> p1b</p>
'''
,
###
'inline link with title'
,
'[text](url "title")','<p><a href="url" title="title">text</a></p>'
,
###
'ref link'
,
'''
a [text][ref1] b

[ref1]: https://example
'''
,
'''
<p>a <a href="https://example">text</a> b</p>
'''
,
###
'emphasis'
,
'a *b c* d','<p>a <em>b c</em> d</p>'
,
###
'strong'
,
'a **b c** d','<p>a <strong>b c</strong> d</p>'
,
###
'code span'
,
'b `c` d','<p>b <code>c</code> d</p>'
,
###
'image'
,
'![alt](url)','<p><img src="url" alt="alt" /></p>'
,
###
'automatic link in p'
,
'a <https://url> b','<p>a <a href="https://url">https://url</a> b</p>'
,
###
'isolated automatic link'
,
'''
<https://url>
''',
'''
<p><a href="https://url">https://url</a></p>
'''
,
###
'backslash escape'
,
'\\*a\\* \\#b','<p>*a* #b</p>'
,
###
'unclosed span'
,
'a *b c','<p>a *b c</p>'
,
###
'masked span ending'
,
'a *b `co* de` d','<p>a *b <code>co* de</code> d</p>'
,

]



class TestMarkdown(unittest.TestCase):
    pass

def make_test(text, expected):
    def test_func(self):
        self.assertEqual(montmark.transform(text).strip(), expected.strip(), msg=text)
    return test_func

nb = 1
for i in range(0, len(tests), 3):
    group = tuple(tests[i:i+3])
    test_name, text, expected = group
    setattr(TestMarkdown, f'test_{nb:03}_{test_name.replace(" ", "_")}', make_test(text, expected))
    nb += 1


