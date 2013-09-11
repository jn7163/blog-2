from tornado.web import RequestHandler
import json

class LoginHandler(RequestHandler):
    def post(self):
        username = self.get_argument("username", default=None)
        password = self.get_argument("password", default=None)
        remember = True if self.get_argument("remember", default=False) == "true" else False

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps({"username": username, 
            "password": password, "remember": remember}))
