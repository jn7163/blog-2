from basehandler import BaseHandler
from bson.objectid import ObjectId
import json
from datetime import datetime
from tornado.web import HTTPError

class EditHandler(BaseHandler):

    def get(self, article_id=None):
        if self.get_logined_user() is None:
            raise HTTPError(404)
        arg = {
            '_id': '',
            'title': '',
            'categories': '',
            'content': '',
            'refurl': '/blog' if not article_id else '/blog/article/%s' % article_id,
            'nav_choose': "blog",
        }

        if article_id:
            article_id = ObjectId(article_id)
            arti = self.db.article.find_one({"_id": article_id})
            if arti:
                arg['title'] = arti['title']
                arti_cats = self.db.category.find({"articles": article_id})
                arg['categories'] = ','.join(cat['name'] for cat in arti_cats)
                arg['content'] = arti['content']
                arg['_id'] = arti['_id']
        self.render("edit.html", **arg)

    def post(self, article_id):
        """ 
            RESTful api 
            argument: title, content, categories
            return {"success": true/false, "msg": "return message"}
        
        """
        if self.get_logined_user() is None:
            raise HTTPError(404)

        resp = {"success": True, "msg": 'ok'}
        article = {
                'title': self.get_argument("title", None),
                'content': self.get_argument("content", None),
            }

        cats = self.get_argument("categories", None)
        if not article['title'] or not article['content'] or not cats:
            resp['success'] = False
            resp['msg'] = "Missing argument"
        else:
            cats = cats.split(',')
            categories = []
            for cat_name in cats:
                catobj = self.db.category.find_one({"name": cat_name})
                if not catobj:
                    catid = self.db.category.insert({"name": cat_name, "articles": []})
                    catobj = self.db.category.find_one({"_id": catid})
                categories.append(catobj)

            try:
                if article_id:
                    """ update article """
                    article_id = ObjectId(article_id)
                    self.db.article.update({"_id": article_id},
                            {"$set": article})
                else:
                    """ insert new article """
                    article['date'] = datetime.today()
                    article_id = self.db.article.insert(article)
                
                for cat in categories:
                    """ update category """
                    if article_id not in cat['articles']:
                        cat['articles'].append(article_id)
                        self.db.category.save(cat)

            except Exception, e:
                resp = {"success": False, "msg": str(e)}

            resp['article_id'] = str(article_id)

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(resp))
