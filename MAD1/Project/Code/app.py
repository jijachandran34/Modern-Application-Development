from flask import Flask
from flask import render_template,redirect,url_for,session
from flask import request

import os

from sqlalchemy.ext.declarative import declarative_base
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func, ForeignKey

from werkzeug.utils import secure_filename
from datetime import timedelta,datetime
from jinja2.filters import FILTERS
import jinja2

# from flask_login import LoginManager,UserMixin
# from flask_login import login_user, login_required, logout_user,current_user

from datetime import datetime
engine = None
Base = declarative_base()
db = SQLAlchemy()

#---------------**********----------------#
#               Models
#---------------**********----------------#

class Users(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String(20),unique=True)
    password = db.Column(db.String(80),nullable=False)
    # email = db.Column(db.String, unique=True)
    created_on = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    # posts = db.relationship('Posts',backref='author',secondary ='association')
 
    userfollow = db.relationship('Followers',foreign_keys= 'Followers.user_id',backref='followed_by')
    userfollower = db.relationship('Followers', foreign_keys= 'Followers.follower', backref='follower_of')

class Posts(db.Model):
    __tablename__ = 'post'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String, unique=True)
    userid = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content=db.Column(db.String)
    image = db.Column(db.String)
    status=db.Column(db.String)
    language= db.Column(db.String)
    user = db.relationship("Users",backref="posts")
    created_on = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_on = db.Column(db.DateTime(timezone=True), onupdate=func.now())

class Followers(db.Model):

    __tablename__ = 'followers'
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id =db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    follower =db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_on = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)


#---------------**********----------------#
#         Create APP & configuration
#---------------**********----------------#
curr_dir = os.path.abspath(os.path.dirname(__file__))
SQLITE_DB_DIR = (curr_dir+ '\db\\')

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + SQLITE_DB_DIR+'bloglite.sqlite3'
allExt = {'png', 'jpg', 'jpeg', 'gif'}
print(SQLALCHEMY_DATABASE_URI)

DEBUG = True
#-------------format date filter page--------------#

def format_date(value,format='%d %B, %Y %H:%M %p '):
    
    return value.strftime(format)

def create_app():

    app = Flask(__name__, template_folder="templates")

    app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] =False
    app.config['SECRET_KEY']='iitmbsmad1'
    app.config['UPLOAD_FOLDER']= curr_dir+"\static\images\\"
    app.config['PERMANENT_SESSION_LIFETIME']= timedelta(hours=3)
    db.init_app(app)
    # print(app.config['PERMANENT_SESSION_LIFETIME'])
    
    app.app_context().push()
    # db.create_all()
    # print("db created")
    
    FILTERS["format_date"] = format_date
    # print(jinja2.Environment().filters)
    
    return app

app = create_app()


#---------------**********----------------#
#               Controllers
#---------------**********----------------#


#-------------index page--------------#
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":    
        return render_template('/index.html')
    
#-------------login and register pages--------------#
@app.route("/login", methods=["GET", "POST"])
def login():
    print("login")
    if request.method =="POST":
        user = Users.query.filter_by(username=request.form["username"]).first()
        
        if user is not None and user.password == request.form["password"]:
            print("user is valid")
            session['user_id']=user.id
            session['user_name']=user.username
            session.permanent = False
            # print( session['user_id'], "logged in")
            return redirect(url_for("userfeed"))
        else:
            return render_template("login.html",error = "Invalid credentials!")
        if user is None:
            # print("no user")
            return redirect(url_for("register"))
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
   
    
    if request.method =="POST":
        print("Signing up user ")
        user = Users.query.filter_by(username=request.form["username"]).first()
        
        if not user:
            newuser = Users()
            newuser.username = request.form["username"]
            newuser.password = request.form["password"]
            
            dbsession = db.session()
            dbsession.add(newuser)
            dbsession.commit()
            print("User created successfully")
   
            return redirect(url_for("login"))
        else:
            return render_template("register.html",error = "Username exists!")
    return render_template("register.html")

@app.route("/logout",methods=["GET", "POST"])
def logout():
    
    session['user_id']=""
    session['user_name']=""
    return redirect(url_for("index"))

#-------------user specific pages--------------#
@app.route("/<user_id>/userprofile",methods=["GET", "POST"])
def userprofile(user_id):
    print("userprofile")
    
    if request.method =="GET":
        # current_user = session['user_id']
        followers = Followers.query.filter_by(user_id=user_id)
        following = Followers.query.filter_by(follower=user_id)
        user = Users.query.filter_by(id=user_id).first()
        posts = Posts.query.filter_by(userid=user_id).all()
        postcount = len(posts)#count()
        followercount = followers.count()#len(followers.count()
        followingcount = following.count()
        # print(len(posts))
        return render_template("/userprofile.html",user=user,posts=posts,postcount=postcount,
                                followercount=followercount, followingcount=followingcount)

@app.route("/userfeed",methods=["GET", "POST"])
def userfeed():
    print("userfeed")
    current_user = session['user_id']
    
    if request.method =="GET":

        following = Followers.query.filter(Followers.follower== current_user).all()
        
        feeds={}
        # print(following)
        for f in following:
           
            userf = Users.query.filter_by(id=f.user_id).first()
            posts =Posts.query.filter_by(userid=f.user_id,status='Public').all()
            if len(posts)>0:
                feeds[userf.id,userf.username]= posts
                feedcnt= len(feeds)
            # print(feeds)
        return render_template("userfeed.html",feeds=feeds) 

#-------------create posts page--------------#
@app.route("/<user_id>/createpost",methods=["GET","POST"])
def createpost(user_id):  

    if request.method =="POST":
        p= Posts()
        print("creating post...")
        if "postTitle" in request.form:
            p.title = request.form["postTitle"]
        if "postContent" in request.form:
            p.content = request.form["postContent"]
        if request.files['imagefile'] :#and request.imagefile.filename!='' :
            imgFilename= request.files['imagefile']
            filename= secure_filename(imgFilename.filename)
            # print("path:",app.config['UPLOAD_FOLDER']+filename)
            imgFilename.save(app.config['UPLOAD_FOLDER']+filename)
            p.image=filename    #app.config['UPLOAD_FOLDER']+filename
        p.userid = user_id
        if request.form.get('poststatus'):
            p.status="Private"
               
        else:
            p.status="Public"
            print(p.status)
        p.language = 'English'

        session = db.session()
        session.add(p)
        session.commit()
        postid =p.id
        print("Committed data",postid)
        return redirect(url_for("userprofile",user_id=user_id))
    
    return render_template("createpost.html")

#-------------Display/Modify/Delete post page--------------#  

@app.route("/displaypost/<user_id>/<post_id>",methods=["GET","POST"])
def displaypost(user_id,post_id):
    print("displaypost")
    # current_user = session['user_id']
    if request.method =="GET":
       
        user = Users.query.filter_by(id=user_id).first()
        post= Posts.query.filter_by(id=post_id).first()
        # print(jinja2.Environment().filters)
        return render_template("displaypost.html",post=post,user=user)

#-------------Modify post--------------#
@app.route("/modify/<user_id>/<post_id>",methods=["GET","POST"])
def modifypost(user_id,post_id):
    print("modifypost")
    current_user = session['user_id']
    if request.method=="GET":
        post = Posts.query.filter_by(userid = user_id , id = post_id).first()
        user = Users.query.filter_by(id=user_id).first()
        return render_template("editpost.html",post=post,user=user)
    
    post = Posts.query.filter_by(userid = user_id , id = post_id).first()
    post.title = request.form["postTitle"]
    post.content= request.form["postContent"]
  
    
    if request.form.get('poststatus'):
        post.status="Private"
        
    else:
        post.status="Public"
        
    if request.files['imagefile'] :#and request.imagefile.filename!='' :
        imgFilename= request.files['imagefile']
        filename= secure_filename(imgFilename.filename)
        print("path:",app.config['UPLOAD_FOLDER']+filename)
        imgFilename.save(app.config['UPLOAD_FOLDER']+filename)
        post.image=filename 
    db.session.commit()
    return redirect(url_for("userprofile",user_id=user_id))


#-------------private post--------------#
@app.route("/makeprivate/<user_id>/<post_id>",methods=["GET","POST"])
def makepostprivate(user_id,post_id):
    print("makepostprivate")
    current_user = session['user_id']
    
    if request.method=="GET":
        post = Posts.query.filter_by(userid = user_id , id = post_id).first()
        post.status= "Private"
        db.session.commit()
        return redirect(url_for("userprofile",user_id=user_id))

#-------------delete post--------------#
@app.route("/delete/<user_id>/<post_id>",methods=["GET","POST"])
def deletepost(user_id,post_id):
    print("deletepost")
    current_user = session['user_id']
    if request.method=="GET":
        delpost = Posts.query.filter_by(userid = user_id , id = post_id).first()
        dbsession = db.session()
        dbsession.delete(delpost)
        dbsession.commit()
        
        return redirect(url_for("userprofile",user_id=user_id))
   
#-------------followers page--------------#  
@app.route("/followers",methods=["GET","POST"])
def followers(): 
    print("followers")
    current_user = session['user_id']
    if request.method =="GET":
        
        followers = Followers.query.filter_by(user_id=current_user).all()
        users=[]
        for f in followers:
            
            u = Users.query.filter_by(id=f.follower).first()
            users.append(u)
            
        return render_template("followers.html",users=users)
    
#-------------following page--------------#  
@app.route("/following",methods=["GET","POST"])
def following(): 

    print("following")
    current_user = session['user_id']
    if request.method =="GET":
        
        following = Followers.query.filter_by(follower=current_user).all()
        users=[]
        for f in following:
            
            u = Users.query.filter_by(id=f.user_id).first()
            users.append(u)
            
        return render_template("following.html",users=users)    
    
#-------------follow user--------------#
@app.route("/follow/<user_id>",methods=["GET","POST"])
def follow(user_id):
    print("follow")
    current_user = session['user_id']
   
    if request.method=="GET":
        alreadyf = Followers.query.filter_by(follower=current_user,user_id = user_id).first()
        if not alreadyf:

            f = Followers()
            # print("follow get")
            # if "userid" in request.form:
            f.user_id =user_id
            f.follower=current_user
            dbsession = db.session()
            dbsession.add(f)
            dbsession.commit()        
            return redirect(url_for("search"))
    return redirect(url_for("search"))

#-------------Unfollow user from search result--------------#
@app.route("/unfollow/<user_id>",methods=["GET","POST"])
def unfollow(user_id):
    print("unfolow",user_id,request.method)
    current_user = session['user_id']
    if request.method=="GET":
        delfollower = Followers.query.filter_by(follower = current_user ,user_id = user_id).first()
        if delfollower:
            dbsession = db.session()
            dbsession.delete(delfollower)
            dbsession.commit()
        
            return redirect(url_for("search"))
            
    return redirect(url_for("search"))
#-------------Unfollow user from userprofile following navigation--------------#      
@app.route("/userprofile/unfollow/<following_id>",methods=["GET","POST"])
def unfollowfromprofile(following_id):
    current_user = session['user_id']
    if request.method=="GET":
        delfollower = Followers.query.filter_by(follower = current_user ,user_id = following_id).first()
        dbsession = db.session()
        dbsession.delete(delfollower)
        dbsession.commit()
        
        return redirect(url_for("following"))

@app.route("/search",methods=["GET","POST"])
def search():
    current_user = session['user_id']
    print("search")
    if request.method == 'POST' and request.form["searchtxt"] !="":
       
        keyword =  request.form["searchtxt"]+'%'
        dbsession = db.session()
       
        users = dbsession.query(Users).filter(Users.id!=current_user, Users.username.like(keyword)).all() 

        following = Followers.query.filter_by(follower=current_user).all()
        f=[]
        for follower in following:
            f.append(follower.user_id)
       
        return render_template("search.html",users=users,following=f)

    return render_template("search.html")


if __name__ == '__main__':
    app.run(debug=True) 

