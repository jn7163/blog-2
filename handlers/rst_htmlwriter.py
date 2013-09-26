# -*- coding:utf8 -*-

"""
reST html Writer
"""

from docutils.writers import html4css1

class Writer(html4css1.Writer):
    def __init__(self):
        super(Writer, self).__init__(self)
        self.translator_class = HTMLTranslator

class HTMLTranslator(html4css1.HTMLTranslator):
    """HTMLTranslator class to redefine some stuff

    - no border for tables by default
    - abbreviations
    """

    def visit_abbreviation(self, node):
        attrs = {}
        if node.hasattr('explanation'):
            attrs['title'] = node['explanation']
        self.body.append(self.starttag(node, 'abbr', '', **attrs))

    def depart_abbreviation(self, node):
        self.body.append('</abbr>')

    def visit_table(self, node):
        classes = ' '.join(['docutils', self.settings.table_style]).strip()
        self.body.append(
            self.starttag(node, 'table', CLASS=classes))

    def depart_table(self, node):
        self.body.append('</table>\n')  

