from basehandler import BaseHandler
import json
import hashlib

class LoginHandler(BaseHandler):
    def get(self):
        self.render("login.html", nav_choose="login", 
                redirect_url=self.request.headers.get("referer"))

    def post(self):
        email = self.get_argument("email", default=None)
        password = self.get_argument("password", default=None)
        remember = True if self.get_argument("remember", default=False) == "true" else False

        response = {"success": True, "msg": "ok"}

        if not email or not password:
            response = {"success": False, "msg": "Missing argument"}
        else:
            user_obj = self.user_login(email, password, remember)
            if user_obj is None:
                response = {"success": False, "msg": "Email or password is invalid"}
            else:
                response['user'] = {
                            'email': user_obj['email'],
                            'screen_name': user_obj['screen_name'],
                            'avatar_url': 'http://www.gravatar.com/avatar/%s?s=64' % hashlib.md5(email).hexdigest(),
                            'is_admin': user_obj['is_admin']
                        }

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(response))
