from basehandler import AjaxBaseHandler
from bson.objectid import ObjectId
import json
from datetime import datetime

class AjaxGetArticleHandler(AjaxBaseHandler):
    def get(self, article_id):
        resp = {"success": True, "msg": "ok"}
        
        query_article = self.db.article.find_one({"_id": ObjectId(article_id)})
        if not query_article:
            resp["success"] = False
            resp["msg"] = "article doesn't exists"
            self.write(resp)
        else:
            art = {
                '_id': str(query_article['_id']),
                'title': query_article['title'],
                'date': query_article['date'].strftime('%Y-%m-%d %H:%M:%S'),
                'content': query_article['content'],
                'categories': [],
            }
            for cat in query_article['categories']:
                cat_obj = self.db.category.find_one({"_id": cat})
                art['categories'].append({
                        '_id': str(cat_obj['_id']),
                        'name': cat_obj['name'],
                    })
            self.write(art)

