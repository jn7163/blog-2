Hola! Welcome
-------------

:date: 2013-12-11 09:49
:tags:
:category: Blog
:slug: my-new-blog
:author: `Y. T. Chung`

This is my new blog, which is powered by Pelican_ and Python3_.

.. _Pelican: http://docs.getpelican.com/
.. _Python3: http://www.python.com/

Why I rewrite my blog?
======================

Previous version of my blog was built from scratch by using Bootstrap_, Flask_ and MongoDB_. It took me about 2 weeks to build the front-end pages. But it was not as perfect as I expected. I want to focus on writing blogs but fix bugs.

.. _Bootstrap: http://getbootstrap.com/
.. _Flask: http://flask.pocoo.org/
.. _MongoDB: http://www.mongodb.org/

My blog used to be a **dynamic blog**, which means it has a server-side program and database. I have to write blogs in browser powered by a code editor CodeMirror_. It is not comfortable to write blogs in that way.

.. _CodeMirror: http://codemirror.net/

This is a **static blog**. I can write my blogs on my computer and generate HTML pages by using one command ``make html``. Then I can upload the generated HTML files to my server. My blog is served without any server-side logic and database.

How I build my blog?
====================

Well, it is pretty easy. First I installed a Python_ environment. Python 2 or 3 are ok. I chose Python 3. Then make a new folder:

.. _Python: http://www.python.com/

.. code:: bash

    $ mkdir myblog

Next I created an isolated Python environment by ``virtualenv`` and installed dependences in requirements.pip (``pelican`` and ``typogrify``).

.. code:: bash

    $ cd myblog
    $ virtualenv .venv
    $ . .venv/bin/activate
    $ pip install -r requirements.pip
    $ pelican-quickstart

After answering a few questions, the blog was created. Create a new file in ``myblog/content`` and write my first blog.

.. code:: rst

    Hola! Welcome
    -------------

    :date: 2013-12-11 09:49
    :tags:
    :category: Blog
    :slug: my-new-blog
    :author: `Y. T. Chung`
    :summary: Short introduction for my new blog.

    This is my new blog, which is powered by Pelican_ and Python3_.

    .. _Pelican: http://docs.getpelican.com/
    .. _Python3: http://www.python.com/

Build HTML pages and serve it.

.. code:: bash

    $ make html
    $ make serve

Well, that is it. I found a lot of themes in HERE_. None of it is my favourite, I will try to make another one.

.. _HERE: https://github.com/getpelican/pelican-themes
