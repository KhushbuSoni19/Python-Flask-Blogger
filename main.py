from flask import Flask, render_template, request, session,redirect
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import json
from flask_mail import Mail
import os
from werkzeug.utils import secure_filename
import math
with open('config.json', 'r') as c:
    params = json.load(c)["params"]


local_server = True

app = Flask(__name__)
app.secret_key = 'super-secret-key'

app.config.update(
    MAIL_SERVER = 'smtp.gmail.com',
    MAIL_PORT = '465',
    MAIL_USE_SSL = True,
    MAIL_USERNAME = params["gmail-user"],
    MAIL_PASSWORD = params["gmail-password"]
)
app.config['UPLOAD_FOLDER'] = params['file_upload_location']
mail = Mail(app)
if(local_server):
    app.config['SQLALCHEMY_DATABASE_URI'] = params['local_URI']
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = params['prod_URI']
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Contacts(db.Model):
   # sno, name, num, msg, email, date

    sno =  db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    Number = db.Column(db.String(20), nullable=False)
    msg = db.Column(db.String(200), nullable=False)
    Email = db.Column(db.String(20), nullable=False)
    DateTime = db.Column(db.String(12))

class Posts(db.Model):

    Sno =  db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(140), nullable=False)
    content = db.Column(db.String(400), nullable=False)
    DateTime = db.Column(db.String(12))
    #slug = db.Column(db.Text, index = True, nullable=False)
    img_file = db.Column(db.String(30), nullable=False)

        #def __init__(self, title, content, DateTime, slug, img_file):
        #self.content = content
        #self.DateTime = DateTime
        #self.slug = slug
        #self.img_file = img_file

@app.route("/")
def home():
    post = Posts.query.filter_by().all()
    last = int(math.ceil(len(post)/int(params['no_of_posts'])))
    #pagination logic will be devided by 2
    page = request.args.get("page")
    if not str(page).isnumeric() :
        page = 1
    page = int(page)
    post = post[(page-1)*int(params['no_of_posts']) : (page-1)*int(params['no_of_posts']) + int(params['no_of_posts'])]
    #pagination logic
    #we are in first page
    if page==1:
        prev = "#"
        next = "/?page="+  str(page+1)

    #we are in last page
    elif page==last:
        prev = "/?page="+ str(page-1)
        next = "#"
    #if we are in middle page
    else:
        prev = "/?page="+ str(page-1)
        next  = "/?page="+ str(page+1)
    #post = Posts.query.filter_by.all()[0:params['no_of_post']]
    return render_template('index.html', params = params,mypost = post, prev = prev, next = next)

@app.route("/about")
def about():
    return render_template('about.html', params = params) #all parameter are going to all the pages

@app.route("/dashboard", methods = ['GET', 'POST'])
def dashboard():

    if 'user' in session and session['user'] == params["admin_username"]:
           post = Posts.query.all()
           return render_template('dashboard.html',params = params, mypost = post)

    if (request.method == 'POST'):
        username = request.form.get('uname')
        password = request.form.get('password')

        if(username == params["admin_username"] and password == params["admin_password"]):
            #set session variable
            session['user'] = username
            post = Posts.query.all()
            return  render_template('dashboard.html',params = params, mypost = post)

    return render_template('login.html', params = params) #all parameter are going to all the pages

@app.route("/contact" ,methods = ['GET', 'POST'])
def contact():
    if(request.method=='POST'):
       #Add entry to the database
        name =  request.form.get("name")
        email = request.form.get("email")
        num= request.form.get("num")
        msg = request.form.get("msg")
        # sno, Name, Number, msg, email, date
        entry = Contacts(name = name,Number = num,msg = msg,Email = email, DateTime = datetime.now())
        db.session.add(entry)
        db.session.commit()
        mail.send_message("NEW Message from " +name,
                        sender= email,
                        recipients = [params[ 'gmail-user' ]],
                        body= msg + "\n" + num
                        )

    return render_template('contact.html', params = params)

@app.route("/post/<Sno>", methods = ["GET", "POST"])
def post1(Sno):
    post = Posts.query.filter_by(Sno = Sno).first()
    return render_template('post.html', params = params ,mypost = post)

@app.route("/edit/<Sno>", methods = ["GET", "POST"])
def edit(Sno):
    if 'user' in session and session['user'] == params["admin_username"]:

        if request.method == "POST":
            title1 = request.form.get('title')
            content = request.form.get('content')
            slug = request.form.get('slug')
            img_file = request.form.get('img_file')
            DateTime = datetime.now()
            if Sno == '0':
                print('4')
                post = Posts(title = title1, content = content, slug = slug, img_file = img_file, DateTime = DateTime)
                print('5')
                db.session.add(post)
                print('6')
                db.session.commit()
                print('7')
                print("successfully Added")
                print('8')

            else:
                post = Posts.query.filter_by(Sno = Sno).first()
                post.title = title1
                post.content = content
                post.slug = slug
                post.img_file = img_file
                post.DateTime = DateTime
                db.session.commit()
                return redirect("/edit/"+Sno)
        post = Posts.query.filter_by(Sno = Sno).first()

        return render_template("edit.html", params = params, post = post, Sno = Sno)
    return render_template('edit.html', params = params, post = post, Sno = Sno)

@app.route("/uploader", methods = ["GET", "POST"] )
def uploader():
    if 'user' in session and session['user'] == params["admin_username"]:
        if(request.method == 'POST'):
            f = request.files['file1']
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(f.filename) ))
            return "upload successfully"

@app.route("/Logout")
def Logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<Sno>", methods = ["GET", "POST"])
def Delete(Sno):
    if 'user' in session and session['user'] == params["admin_username"]:
        post = Posts.query.filter_by(Sno = Sno).first()
        db.session.delete(post)
        db.session.commit()
    return redirect('/dashboard')

app.run(debug=True)
