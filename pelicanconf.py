#!/usr/bin/env python
# -*- coding: utf-8 -*- #

AUTHOR = 'Jethro Cao'
SITENAME = "Jethro's Tech Blog"
SITEURL = ''

PATH = 'content'
OUTPUT_PATH = 'docs'

TIMEZONE = 'America/Toronto'

DEFAULT_LANG = 'en'

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Blogroll
LINKS = (('Pelican', 'https://getpelican.com/'),)

# Social widget
SOCIAL = (('GitHub', 'https://github.com/jyscao'),
          ('Reddit', 'https://www.reddit.com/user/jyscao'),
          ('Medium', 'https://medium.com/@jyscao'),)

DEFAULT_PAGINATION = False

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True

DELETE_OUTPUT_DIRECTORY = True
OUTPUT_RETENTION = ['CNAME']
