from basehandler import BaseHandler
import json
import hashlib

class RegisterHandler(BaseHandler):
    def post(self):
        email = self.get_argument("email", default=None)
        password = self.get_argument("password", default=None)
        name = self.get_argument("name", default=None)

        response = {'success': True, 'msg': 'ok'}

        if not email or not password or not name:
            response = {'success': False, 'msg': 'Missing Argument'}
        else:
            exist_user = self.db.user.find_one({"email": email})
            if exist_user is None:
                user = {
                    'email': email,
                    'password': hashlib.md5(password).hexdigest(),
                    'screen_name': name,
                    'encrypt': 'sha1',
                    'is_admin': False,
                }
                self.db.user.insert(user)
            else:
                response = {'success': False, 'msg': 'User %s already exists' % email}
                
        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(response))
