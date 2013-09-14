from basehandler import BaseHandler
import markdown
import hashlib
from bson.objectid import ObjectId
from tornado.web import HTTPError

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
            'content': markdown.markdown(query_result["content"], 
                extensions=["codehilite(guess_lang=False)"]),
            'categories': self.db.category.find({"articles": article_id}),
            'comments': [],
            'comment_count': self.db.comment.find({"article": article_id}).count(),
        }
        for comment in self.db.comment.find({"article": article_id, "replyto": None}):
            query_user = self.db.user.find_one({"_id": comment["user"]})
            comments = {
                'user': {
                    'screen_name': query_user['screen_name'],
                    'avatar_url': 'http://www.gravatar.com/avatar/%s?s=64' % hashlib.md5(query_user["account"]).hexdigest(),
                },
                'date': comment["date"],
                'content': comment["content"],
                'replys': [],
                'support_num': len(comment['supportedby']),
                'oppose_num': len(comment['opposedby']),
            }
            for reply in self.db.comment.find({"replyto": comment["_id"]}):
                query_reply_user = self.db.user.find_one({"_id": reply["user"]})
                comments['replys'].append({
                        'user': {
                            'screen_name': query_reply_user['screen_name'],
                            'avatar_url': 'http://www.gravatar.com/avatar/%s?s=64' % hashlib.md5(query_reply_user["account"]).hexdigest(),
                        },
                        'date': reply['date'],
                        'content': reply['content'],
                        'support_num': len(reply['supportedby']),
                        'oppose_num': len(reply['opposedby']),
                    })
            article['comments'].append(comments)
        
        self.render("article.html", article=article, 
                sidebar=self.get_sidebar_data(), nav_choose="blog")
