from basehandler import BaseHandler
from tornado.web import HTTPError
from bson.objectid import ObjectId

class CategoryHandler(BaseHandler):
    def get(self, tag_id):
        cat = self.db.category.find_one({"_id": ObjectId(tag_id)})
        if not cat:
            raise HTTPError(404)

        category = {
            'name': cat["name"],
        }

        articles = [self.db.article.find_one({"_id": article_id}) for article_id in cat["articles"]]
        articles.sort(cmp=lambda x, y: x["date"] < y["date"], reverse=True)
        article_dict = {}
        for art in articles:
            art["categories"] = self.db.category.find({"articles": art["_id"]})
            art["comment_count"] = self.db.comment.find({"article": art["_id"]}).count()
            if not article_dict.has_key(art["date"].year):
                article_dict[art["date"].year] = []
            article_dict[art["date"].year].append(art)

        category["articles"] = article_dict
        category["year"] = sorted(article_dict, reverse=True)

        self.render("category.html", sidebar=self.get_sidebar_data(), category=category,
                nav_choose="blog")
