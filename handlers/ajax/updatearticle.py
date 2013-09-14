from basehandler import AjaxBaseHandler
from bson.objectid import ObjectId
from datetime import datetime

class AjaxUpdateArticleHandler(AjaxBaseHandler):
    def post(self, article_id):
        response = {
            'success': True,
            'msg': "ok"
        }
        try:
            updobj = {
                'title': self.get_argument("title", default=None),
                'categories': [],
                'content': self.get_argument("content", default=None),
                'date': datetime.today()
            }
            tags = self.get_argument("categories", default=None)
            if not updobj["title"] or not updobj["content"] or not tags:
                response["success"] = False
                response["msg"] = "miss argument"
                self.write(response, 400)
                return

            tags = tags.split(',')
            for tag in tags:
                tagobj = self.db.category.find_one({"name": tag})
                if not tagobj:
                    self.db.category.insert({"name": tag, "articles": [ObjectId(article_id), ]})
                    tagobj = self.db.category.find_one({"name": tag})
                
                updobj["categories"].append(tagobj["_id"])

            self.db.article.update({"_id": ObjectId(article_id)},
                    {
                        "$set": updobj   
                    })
            self.write(response)
        except:
            response["success"] = False
            response["msg"] = "argument_error"
            self.write(response, 400)

