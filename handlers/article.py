from basehandler import BaseHandler
from bson.objectid import ObjectId
from tornado.web import HTTPError
from docutils.core import publish_parts
from rst_htmlwriter import Writer

class ArticleHandler(BaseHandler):
    def get(self, article_id):
        article_id = ObjectId(article_id)
        query_result = self.db.article.find_one({"_id": article_id})
        if not query_result:
            raise HTTPError(404)
        article = {
            '_id': query_result["_id"],
            'title': query_result["title"],
            'date': query_result["date"],
            'content': publish_parts(query_result['content'], 
                writer=Writer(),
                settings_overrides={
                        'initial_header_level': 2,
                    })['html_body'],
            'categories': self.db.category.find({"articles": article_id}),
        }
        
        self.render("article.html", article=article, 
                sidebar=self.get_sidebar_data(), nav_choose="blog")
