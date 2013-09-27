from basehandler import BaseHandler
import pymongo
import re
from docutils.core import publish_parts
from rst_htmlwriter import Writer

class BlogHandler(BaseHandler):
    def get(self):
        query_result = self.db.article.find().sort("date", pymongo.DESCENDING)
        articles = []
        regx = re.compile(r'<img.*?src="(.*)".*?>')
        carousels = []

        if query_result.count() > 0:
            for ar in query_result[:5]:
                article = {
                        '_id': ar["_id"],
                       'title': ar["title"],
                       'date': ar["date"],
                       'content': publish_parts(ar['content'], writer=Writer())['html_body'],
                       'categories': list(self.db.category.find({"articles": ar['_id']})),
                   }
                articles.append(article)

            for ar in articles:
               imgs = regx.findall(ar["content"])
               if len(imgs) != 0:
                   carousels.append({
                           '_id': ar["_id"],
                           'title': ar["title"],
                           'img': imgs[0],
                           'categories': ar["categories"],
                           'date': ar["date"],
                       })

        self.render("blog.html", 
                sidebar=self.get_sidebar_data(), articles=articles, carousels=carousels[:4],
                nav_choose="blog")

