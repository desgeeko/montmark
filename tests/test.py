import unittest
import montmark

tests = [

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
'atx header'
,
'## t2','<h2>t2</h2>'
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
'''
,
'''
<blockquote>
<h1>t1</h1>
</blockquote>
'''
,
###
'simple unordered list'
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
'automatic link'
,
'a <https://url> b','<p>a <a href="https://url">https://url</a> b</p>'
,
###
'backslash escape'
,
'\\*a\\*','<p>*a*</p>'
,


]



class TestMarkdown(unittest.TestCase):
    pass

def make_test(text, expected):
    def test_func(self):
        self.assertEqual(montmark.transform(text).strip(), expected.strip(), msg=text)
    return test_func

for i in range(0, len(tests), 3):
    group = tuple(tests[i:i+3])
    test_name, text, expected = group
    setattr(TestMarkdown, f'test_{test_name.replace(" ", "_")}', make_test(text, expected))


