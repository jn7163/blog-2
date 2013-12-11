#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'Y. T. Chung'
SITENAME = 'YTBlog'
SITEURL = ''

TIMEZONE = 'Asia/HongKong'

DEFAULT_LANG = 'en'

CONTACT_EMAIL = "zonyitoo@gmail.com"

USE_CUSTOM_MENUITEMS = True

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
