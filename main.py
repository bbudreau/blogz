from flask import Flask, request, redirect, render_template, session
from flask_sqlalchemy import SQLAlchemy
from hashutils import make_pw_hash, check_pw_hash


app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:MyNewPass@localhost:8889/blogz'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)
app.secret_key = 'l33t'
class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120))
    body = db.Column(db.String(1000))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))
        

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner


class User(db.Model):
    id =db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True)
    pw_hash = db.Column(db.String(120))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.pw_hash = make_pw_hash(password)


@app.before_request
def require_login():
    allowed_routes = ['login', 'signup', 'blog', 'index', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/')
def index():
    users = User.query.all()
    return render_template('index.html', users=users)


@app.route('/login', methods=['POST' , 'GET'])
def login():
    username_error = ""
    password_error = ""

    if request.method == 'POST':
        password = request.form['password']
        username = request.form['username']
        user = User.query.filter_by(username=username).first()

        if user and check_pw_hash(password, user.pw_hash):
            session['username'] = username
            return redirect('add_post')
        if not user:
            return render_template('login.html', username_error="Username does not exist")
        else:
            return render_template('login.html', password_error="Your username and password were incorrect")
    return render_template('login.html')

@app.route('/signup', methods=['POST' , 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']
        exist = User.query.filter_by(username=username).first()

        username_error = ""
        password_error = ""
        verify_error = ""

        if username == "":
            username_error = "Please enter a username."
        elif len(username) <=3 or len(username) > 20:
            username_error = "Username must be between 3 and 20 characters."
        elif " " in username:
            username_error = "Username cannot contain spaces."
        if password == "":
            password_error = "Please enter a password."
        elif len(password) <= 3:
            password_error = "Password must be greater than 3 characters."
        elif " " in password:
            password_error = "No spaces allowed in password."
        if password != verify or verify == "":
            verify_error = "Passwords do not match."
        if exist:
            username_error = "Username already taken."
        if len(username) > 3 and len(password) > 3 and password == verify and not exist:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/add_post')
        else:
            return render_template('signup.html', 
            username=username, 
            username_error=username_error,
            password_error=password_error,
            verify_error=verify_error)
    return render_template('signup.html')




@app.route('/blog')
def blog():
    blog_id = request.args.get('id')
    user_id = request.args.get('userid')

    posts = Blog.query.all()


    if blog_id:
        post = Blog.query.filter_by(id=blog_id).first()
        return render_template('single_post.html', title=post.title, body=post.body, user=post.owner.username, user_id=post.owner_id)
    if user_id:
        entries = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('user.html', entries=entries)

    return render_template('blog.html', posts=posts)


@app.route("/add_post")
def add_post():
    return render_template('add_post.html', title="Add a New Blog Entry")

@app.route("/add_post", methods=['POST', 'GET'])

def verify_add_post():
    title = request.form['title']
    body = request.form['body']
    owner = User.query.filter_by(username=session['username']).first()

    title_error = ''
    body_error = ''

    if title == "":
        title_error = "Title needed"
    if body == "":
        body_error = "Blog content required"
    if not title_error and not body_error:
        new_blog = Blog(title, body, owner)
        db.session.add(new_blog)
        db.session.commit()
        page_id = new_blog.id
        return redirect('/blog?id={0}'.format(page_id))
    else:
        return render_template('add_post.html', title=title, body=body, title_error=title_error, body_error=body_error)

@app.route('/logout')
def logout():
    del session['username']
    return redirect('/')


if __name__ == '__main__':
    app.run()

        


