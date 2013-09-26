from basehandler import BaseHandler
import json

class UploadHandler(BaseHandler):
    def post(self):
        imgfile = self.request.files['img']

        response = {"success": True, "msg": "ok"}

        try:
            img = imgfile[0]
            imgf = open('media/' + img['filename'], 'w')
            imgf.write(img['body'])
            imgf.close()
            response['img'] = '/media/' + img['filename']
        except Exception, e:
            response['success'] = False
            response['msg'] = str(e)

        self.set_header("Content-Type", "application/json")
        self.write(json.dumps(response))
