from pelican.readers import PelicanHTMLTranslator
from pelican.readers import RstReader
import docutils


class CustomHTMLTranslator(PelicanHTMLTranslator):

    def visit_table(self, node):
        classes = ' '.join(['docutils',
                           'table', 'table-hover', 'table-bordered',
                           self.settings.table_style]).strip()
        self.body.append(
            self.starttag(node, 'table', CLASS=classes))

    def depart_table(self, node):
        self.body.append('</table>\n')


class CustomRstReader(RstReader):

    def _get_publisher(self, source_path):
        extra_params = {'initial_header_level': '2',
                        'syntax_highlight': 'short',
                        'input_encoding': 'utf-8'}
        user_params = self.settings.get('DOCUTILS_SETTINGS')
        if user_params:
            extra_params.update(user_params)

        pub = docutils.core.Publisher(
            destination_class=docutils.io.StringOutput)
        pub.set_components('standalone', 'restructuredtext', 'html')
        pub.writer.translator_class = CustomHTMLTranslator
        pub.process_programmatic_settings(None, extra_params, None)
        pub.set_source(source_path=source_path)
        pub.publish()
        return pub
