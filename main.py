from tornado.web import Application
from tornado.ioloop import IOLoop

from handlers.index import IndexHandler
from handlers.blog import BlogHandler
from handlers.login import LoginHandler

import os

settings = {
    'static_path': os.path.join(os.path.dirname(__file__), "static"),
    'template_path': os.path.join(os.path.dirname(__file__), "templates"),
    'login_url': '/login',
}

if __name__ == "__main__":
    application = Application([
            (r"/", IndexHandler),
            (r"/blog", BlogHandler),
            (r"/user/login", LoginHandler),
        ], **settings)
    application.listen(8888)

    IOLoop.instance().start()
