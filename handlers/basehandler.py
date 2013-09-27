from tornado.web import RequestHandler
import pymongo
import hashlib

class BaseHandler(RequestHandler):
    def initialize(self):
        self.require_setting('database')
        self.db = self.settings['database']

    def get_sidebar_data(self):
        sidebar = {
            'tags': self.db.category.find(),
            'recently_articles': list(self.db.article.find().sort("date", pymongo.DESCENDING)[:5]),
        }

        for rec_art in sidebar['recently_articles']:
            rec_art['comment_count'] = self.db.comment.find({"article": rec_art["_id"]}).count()

        return sidebar

    def validate_user(self, email, password):
        """
            @return (isValid, userExists)
        """
        user_obj = self.db.user.find_one({"email": email})

        if user_obj is None:
            return (False, False)
        else:
            pwd = ''
            if user_obj['encrypt'] == 'md5':
                pwd = hashlib.md5(password).hexdigest()
            elif user_obj['encrypt'] == 'sha1':
                pwd = hashlib.sha1(password).hexdigest()

            if pwd == user_obj['password']:
                return (True, True)
            else:
                return (False, True)

    def user_login(self, email, password, remember=True):
        valid, exists = self.validate_user(email, password)
        if not valid or not exists:
            return None
        
        if remember:
            self.set_secure_cookie("_u", email)
        else:
            self.set_secure_cookie("_u", email, expires_days=None)

        return self.db.user.find_one({"email": email})

    def user_logoff(self):
        self.clear_cookie("_u")

    def get_logined_user(self):
        #uemail = self.get_cookie("_u")
        #if uemail is None:
        uemail = self.get_secure_cookie("_u")

        if uemail is None:
            return None

        user_obj = self.db.user.find_one({"email": uemail})
        if user_obj is None:
            return None
        return user_obj
            
    def render(self, template_name, **kwargs):
        super(BaseHandler, self).render(template_name, 
                _user=self.get_logined_user(), **kwargs)
