#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Y. T. Chung'
SITENAME = 'YTBlog'
SITEURL = 'http://zonyitoo.me'

RELATIVE_URL = False

TIMEZONE = 'Asia/HongKong'

DEFAULT_LANG = 'zh'

CONTACT_EMAIL = "zonyitoo@gmail.com"

USE_CUSTOM_MENUITEMS = True
DEFAULT_CATEGORY = 'Misc'

ARTICLE_URL = 'blog/{slug}.html'
ARTICLE_SAVE_AS = 'blog/{slug}.html'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None

# Blogroll
LINKS = (('Pelican', 'http://getpelican.com/'),
         ('Python.org', 'http://python.org/'),
         ('Jinja2', 'http://jinja.pocoo.org/'),
         ('You can modify those links in your config file', '#'),)

# Social widget
SOCIAL = (('twitter', 'https://twitter.com/zonyitoo'),
          ('github', 'https://github.com/zonyitoo'),
          ('facebook', 'https://www.facebook.com/yutang.chung.7'))

DEFAULT_PAGINATION = 10

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

# Themes
THEME = "theme/pelican-bootstrap3"
#TYPOGRIFY = True

GITHUB_USER = "zonyitoo"
GITHUB_SHOW_USER_LINK = True

DISQUS_SITENAME = "zonyitooblog"

MENUITEMS = (('About', '/intro.html'),)
TEMPLATE_PAGES = {
    "htmls/intro.html": "intro.html"
}

STATIC_PATHS = [
    'static',
]

EXTRA_PATH_METADATA = {
    'static': {'path': 'static'},
    'favicon.ico': {'path': 'static/img/favicon.ico'},
}

import sys
sys.path.append(".")
from rst_reader import CustomRstReader
READERS = {
    "rst": CustomRstReader,
    "html": None,
}
