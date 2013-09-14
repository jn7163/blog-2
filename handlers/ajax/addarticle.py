from basehandler import AjaxBaseHandler
from datetime import datetime

class AjaxAddArticleHandler(AjaxBaseHandler):
    def post(self):
        print 'here'
        title = self.get_argument("title", None)
        tags = self.get_argument("categories", '')
        content = self.get_argument("content", "")

        response = {
                'success': True,
                'msg': "ok"
            }

        print title
        if not title:
            response['success'] = False
            response["msg"] = "title missed"
            self.write(response, 400)
            return

        print title, tags

        new_post = {
                'title': title,
                'categories': [],
                'content': content,
                'date': datetime.today(),
                'comment_count': 0,
                'comments': [],
            }

        tags = tags.split(',')
        for tag in tags:
            cat = self.db.category.find_one({"name": tag})
            if not cat:
                new_id = self.db.category.insert({"name": tag, "articles": []})
            else:
                new_id = cat["_id"]

            new_post["categories"].append(new_id)

        post_id = self.db.article.save(new_post)
        for cat_id in new_post["categories"]:
            cat = self.db.category.find_one({"_id": cat_id})
            cat["articles"].append(post_id)
            self.db.category.save(cat)

        self.write(response)
