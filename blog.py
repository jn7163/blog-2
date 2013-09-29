from flask import Flask
from flask import render_template
from flask import send_from_directory
from flask import abort
from flask import url_for
from flask import session
from flask import redirect
from flask import request
from flask.json import jsonify
from flask import g

import os
import pymongo
import re
import hashlib

from docutils.core import publish_parts
from rst_htmlwriter import Writer

from bson.objectid import ObjectId

app = Flask(__name__)
app.config['MEDIA_FOLDER'] = os.path.join(os.path.dirname(__file__), 'media')
app.config['DATABASE'] = 'mongodb://localhost:27017'
app.secret_key = '81c970b4e3ec500e0807073db064f15a45d3c3c4'

@app.before_request
def before_request():
    g.db = pymongo.MongoClient(app.config['DATABASE']).ytblog

@app.teardown_request
def after_request(exception):
    g.db.connection.close()

def get_sidebar_data():
    sidebar = {
            'tags': g.db.category.find(),
            'recently_articles': list(g.db.article.find().sort("date", pymongo.DESCENDING)[:5]),
        }
    return sidebar

def get_nav_data():
    userobj = get_logined_user()
    navdata = {
            'tags': g.db.category.find(),
            'user': {'screen_name': userobj['screen_name'],
                'avatar_url': "http://www.gravatar.com/avatar/%s?s=32" % hashlib.md5(userobj['email']).hexdigest()}
                if userobj else None
        }
    return navdata

@app.route("/")
def index():
    return render_template("index.html", 
            nav_choose="home",
            nav_data=get_nav_data())

@app.route("/blog", methods=["GET"])
def blog():
    query_result = g.db.article.find().sort("date", pymongo.DESCENDING)
    #regx = re.compile(r'<img.*?src="(.*)".*?>')
    regx = re.compile(r'.. image::(.*)')
    carousels = []

    for ar in query_result:
        imgs = regx.findall(ar["content"])
        if len(imgs) != 0:
            carousels.append({
                '_id': ar["_id"],
                'title': ar["title"],
                'img': imgs[0].strip(),
                'categories': [{'name': cat['name']}
                    for cat in g.db.category.find({"articles": ar['_id']})],
                'date': ar["date"]
                })
        if len(carousels) >= 4: break

    return render_template('blog.html', 
            sidebar=get_sidebar_data(),
            carousels=carousels[:4],
            nav_choose="blog",
            nav_data=get_nav_data())

@app.route("/blog/article/<article_id>", methods=["GET"])
def article(article_id):
    article_id = ObjectId(article_id)
    query_result = g.db.article.find_one({"_id": article_id})
    if not query_result:
        abort(404)

    article = {
        '_id': query_result["_id"],
        'title': query_result["title"],
        'date': query_result["date"],
        'content': publish_parts(query_result['content'], 
            writer=Writer(),
            settings_overrides={
                    'initial_header_level': 2,
                })['html_body'],
        'categories': g.db.category.find({"articles": article_id}),
    }
    
    return render_template('article.html', article=article, 
            sidebar=get_sidebar_data(), nav_choose="blog",
            nav_data=get_nav_data())

@app.route("/blog/ajax/get/article", methods=["GET"])
def ajax_get_article():
    page = 0
    count = 5
    try:
        if 'page' in request.args:
            page = int(request.args['page']) - 1
        if 'count' in request.args:
            count = int(request.args['count'])

        if page < 0:
            raise Exception()
    except:
        return jsonify(success=False, errmsg="argument error")

    q = g.db.article.find().sort("date", pymongo.DESCENDING)
    resp = {
        'success': True,
        'errmsg': 'ok',
        'articles': []
    }
    if q.count() != 0:
        q = q[page * count: (page + 1) * count]
        resp['articles'] = [
                    {'title': ar['title'], 'content': publish_parts(ar['content'], 
                                                    writer=Writer(),
                                                    settings_overrides={'initial_header_level': 2})['html_body'],
                        'date': ar['date'].strftime("%b %d").upper(), '_id': str(ar['_id']),
                        'categories': [
                            {'name': cat['name'], '_id': str(cat['_id'])} 
                                for cat in g.db.category.find({"articles": ar['_id']})
                            ]}
                    for ar in q
                ]

    return jsonify(**resp)

@app.route("/blog/edit/<article_id>", methods=["GET", "POST"])
def edit(article_id=None):
    if not get_logined_user():
        return redirect(url_for('login'))

    if request.method == "GET":
        arg = {
            '_id': '',
            'title': '',
            'categories': '',
            'content': '',
            'nav_choose': "admin",
            'nav_data': get_nav_data()
        }

        article_id = ObjectId(article_id)
        arti = g.db.article.find_one({"_id": article_id})
        if arti:
            arg['title'] = arti['title']
            arti_cats = g.db.category.find({"articles": article_id})
            arg['categories'] = ','.join(cat['name'] for cat in arti_cats)
            arg['content'] = arti['content']
            arg['_id'] = arti['_id']
        return render_template('edit.html', **arg)
    else:
        """ 
            RESTful api 
            argument: title, content, categories
            return {"success": true/false, "msg": "return message"}
        
        """
        if 'title' not in request.form \
            or 'content' not in request.form \
            or 'categories' not in request.form:
                return jsonify(success=False, errmsg='missing argument')

        article = {
                'title': request.form['title'],
                'content': request.form['content']
            }

        cats = request.form['categories']
        cats = cats.split(',')
        categories = []
        for cat_name in cats:
            catobj = g.db.category.find_one({"name": cat_name.strip()})
            if not catobj:
                catid = g.db.category.insert({"name": cat_name.strip(), "articles": []})
                catobj = g.db.category.find_one({"_id": catid})
            categories.append(catobj)

        try:
            if article_id:
                """ update article """
                article_id = ObjectId(article_id)
                g.db.article.update({"_id": article_id},
                        {"$set": article})
            
            for cat in categories:
                """ update category """
                if article_id not in cat['articles']:
                    cat['articles'].append(article_id)
                    g.db.category.save(cat)

        except Exception, e:
            return jsonify(success=False, errmsg=str(e))

        return jsonify(success=True, errmsg='ok', article_id=str(article_id))

@app.route("/blog/newpost", methods=["GET", "POST"])
def newpost():
    if not get_logined_user():
        return redirect(url_for('login'))

    if request.method == "GET":
        return render_template('edit.html', nav_choose="admin",
                nav_data=get_nav_data())

    else:
        """ 
            RESTful api 
            argument: title, content, categories
            return {"success": true/false, "errmsg": "return message"}
        
        """
        if 'title' not in request.form \
            or 'content' not in request.form \
            or 'categories' not in request.form:
                return jsonify(success=False, errmsg='missing argument')

        article = {
                'title': request.form['title'],
                'content': request.form['content']
            }

        cats = request.form['categories']
        cats = cats.split(',')
        categories = []
        for cat_name in cats:
            catobj = g.db.category.find_one({"name": cat_name.strip()})
            if not catobj:
                catid = g.db.category.insert({"name": cat_name.strip(), "articles": []})
                catobj = g.db.category.find_one({"_id": catid})
            categories.append(catobj)

        try:
            """ insert new article """
            article['date'] = datetime.today()
            article_id = g.db.article.insert(article)
            
            for cat in categories:
                """ update category """
                if article_id not in cat['articles']:
                    cat['articles'].append(article_id)
                    g.db.category.save(cat)

        except Exception, e:
            return jsonify(success=False, errmsg=str(e))

        return jsonify(success=True, errmsg='ok', article_id=str(article_id))


    pass

@app.route("/blog/category/<tag_id>", methods=["GET"])
def category(tag_id):
    cat = g.db.category.find_one({"_id": ObjectId(tag_id)})
    if not cat:
        abort(404)

    category = {
            'name': cat["name"],
        }

    articles = [g.db.article.find_one({"_id": article_id}) for article_id in cat["articles"]]
    articles.sort(cmp=lambda x, y: x["date"] < y["date"], reverse=True)
    article_dict = {}
    for art in articles:
        art["categories"] = g.db.category.find({"articles": art["_id"]})
        art["comment_count"] = g.db.comment.find({"article": art["_id"]}).count()
        if not article_dict.has_key(art["date"].year):
            article_dict[art["date"].year] = []
        article_dict[art["date"].year].append(art)

    category["articles"] = article_dict
    category["year"] = sorted(article_dict, reverse=True)

    return render_template('category.html',
            category=category,
            nav_choose="blog",
            nav_data=get_nav_data())

@app.route("/blog/upload", methods=["POST"])
def upload():
    pass

@app.route("/blog/archive", methods=["GET"])
def archive():
    archives = {}

    for a in g.db.article.find().sort("date", pymongo.DESCENDING):
        article = {
                'title': a['title'],
                'categories': g.db.category.find({"articles": a["_id"]}),
                'date': a['date'],
                "_id": a["_id"]
            }
        if archives.has_key(a['date'].year):
            archives[a['date'].year].append(article)
        else:
            archives[a['date'].year] = [article,];

    return render_template('archive.html', nav_choose="blog",
            archives=archives,
            nav_data=get_nav_data())

@app.route("/blog/admin")
def admin():
    if 'uid' in session:
        return redirect(url_for('admin_users'))
    else:
        return redirect(url_for('login'))

@app.route('/blog/admin/articles')
def admin_articles():

    if 'uid' not in session:
        return redirect(url_for('login'))
    
    return render_template('admin-articles.html', nav_choose="admin",
            nav_data=get_nav_data())

import dateutil.parser
from datetime import datetime
@app.route('/blog/ajax/get/admin/articles')
def ajax_admin_get_articles():
    if 'uid' not in session:
        return jsonify(success=False, errmsg='not logined')

    if 'date' not in request.args:
        return jsonify(success=False, errmsg='argument error')
    date = request.args['date']
    try:
        date = date[:date.rfind("GMT")]
        dobj = dateutil.parser.parse(date)
        if dobj.month == 12:
            ltdobj = datetime(dobj.year + 1, 1, 1)
        else:
            ltdobj = datetime(dobj.year, dobj.month + 1, 1)

        articles = g.db.article.find({"date": {"$gte": dobj, "$lt": ltdobj}})

        return jsonify(success=True, errmsg="ok", articles=[
            {'title': ar['title'], '_id': str(ar['_id']), 'date': ar['date'].strftime("%b %d").upper(),
                'tags': [
                        {'name': tag['name'], '_id': str(tag['_id'])}
                        for tag in g.db.category.find({"articles": ar['_id']})
                    ]}
                for ar in articles
            ])
    except Exception, e:
        return jsonify(success=False, errmsg=str(e))

    return jsonify(success=True, errmsg='ok')

@app.route('/blog/admin/users')
def admin_users():
    if 'uid' not in session:
        return redirect(url_for('login'))

    admin_data = {
            'users': g.db.user.find(),
        }

    return render_template('admin-users.html', nav_choose="admin",
            nav_data=get_nav_data(), admin_data=admin_data)


def user_validate(email, password):
    
    user_obj = g.db.user.find_one({"email": email})
    if not user_obj:
        return None
    else:
        if user_obj['encrypt'] == 'md5':
            pwd_enc = hashlib.md5(password).hexdigest()
        elif user_obj['encrypt'] == 'sha1':
            pwd_enc = hashlib.sha1(password).hexdigest()
        else:
            pwd_enc = password

        if pwd_enc == user_obj['password']:
            return user_obj
        else:
            return None

def get_logined_user():
    if 'uid' in session:
        uid = session['uid']
        userobj = g.db.user.find_one({"_id": ObjectId(uid)})
        return userobj
    else:
        return None

@app.route("/blog/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template('login.html', 
                nav_choose="admin",
                nav_data=get_nav_data())
    else:
        email = request.form['email']
        password = request.form['password']

        response = {"success": True, "msg": "ok"}

        if not email or not password:
            response = {"success": False, "msg": "Missing argument"}
        else:
            user_obj = user_validate(email, password)
            if user_obj is None:
                response = {"success": False, "msg": "Email or password is invalid"}
            else:
                session.permanent = False

                session['uid'] = str(user_obj['_id'])

                response['user'] = {
                            'email': user_obj['email'],
                            'screen_name': user_obj['screen_name'],
                            'avatar_url': 'http://www.gravatar.com/avatar/%s?s=64' % hashlib.md5(email).hexdigest(),
                            'is_admin': user_obj['is_admin']
                        }

        return jsonify(**response)


@app.route("/blog/admin/logout", methods=["GET"])
def logout():
    session.pop('uid', None)
    return redirect(url_for('login'))

@app.route("/media/<filename>", methods=["GET"])
def media(filename):
    return send_from_directory(app.config['MEDIA_FOLDER'],
            filename)

if __name__ == "__main__":
    app.debug = True
    app.run(port=9030)
