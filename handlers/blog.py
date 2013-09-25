from basehandler import BaseHandler
import pymongo
import re
from docutils.core import publish_parts

class BlogHandler(BaseHandler):
    def get(self):
        query_result = self.db.article.find().sort("date", pymongo.DESCENDING)
        page_cnt = (query_result.count() + 4) / 5
        articles = []
        regx = re.compile(r'<img.*?src="(.*)".*?>')
        carousels = []

        current_page = int(self.get_argument("page", 0))
        if current_page >= page_cnt:
            current_page = page_cnt - 1
        
        for ar in query_result[current_page * 5:(current_page + 1) * 5]:
            article = {
                    '_id': ar["_id"],
                   'title': ar["title"],
                   'date': ar["date"],
                   'content': publish_parts(ar['content'], writer_name='html')['html_body'],
                   'categories': self.db.category.find({"articles": ar['_id']}),
                   'comment_count': self.db.comment.find({"article": ar['_id']}).count()
               }
            articles.append(article)

        for ar in articles:
           imgs = regx.findall(ar["content"])
           if len(imgs) != 0:
               carousels.append({
                       '_id': ar["_id"],
                       'title': ar["title"],
                       'img': imgs[0],
                       'categories': article["categories"],
                       'date': article["date"],
                   })

        self.render("blog.html", 
                sidebar=self.get_sidebar_data(), articles=articles, carousels=carousels[:4],
                nav_choose="blog", prev_page=-1 if current_page == 0 else current_page - 1,
                next_page=-1 if current_page == page_cnt - 1 else current_page + 1)
