from basehandler import BaseHandler

class LogoffHandler(BaseHandler):
    def get(self):
        self.user_logoff()
        self.redirect("/user/login")

