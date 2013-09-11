from tornado.web import RequestHandler

class BlogHandler(RequestHandler):
    def get(self):
        self.render("blog.html")
