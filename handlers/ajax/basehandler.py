from tornado.web import RequestHandler
import json

class AjaxBaseHandler(RequestHandler):
    def initialize(self):
        self.require_setting('database')
        self.db = self.settings['database']

    def write(self, chunk, statuscode=200):
        self.set_header("Content-Type", "application/json")
        self.set_status(statuscode)
        resp = json.dumps(chunk)
        super(AjaxBaseHandler, self).write(resp)
