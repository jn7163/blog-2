from basehandler import BaseHandler
from bson.code import Code
import pymongo

class ArchiveHandler(BaseHandler):
    def get(self):

        archives = {}

        for a in self.db.article.find().sort("date", pymongo.DESCENDING):
            article = {
                    'title': a['title'],
                    'categories': self.db.category.find({"articles": a["_id"]}),
                    'date': a['date'],
                    "_id": a["_id"]
                }
            if archives.has_key(a['date'].year):
                archives[a['date'].year].append(article)
            else:
                archives[a['date'].year] = [article,];

        self.render('archive.html', archives=archives, nav_choose="blog")


