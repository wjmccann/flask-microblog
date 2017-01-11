from flask import render_template, flash, redirect, session, url_for, request, g
from app import app, db
from .forms import LoginForm, SignupForm, EditForm, PostForm
from flask_login import login_required, login_user, current_user, logout_user, confirm_login, login_fresh
from .models import User, Post
from datetime import datetime
from werkzeug.utils import secure_filename
import os, shutil
from config import POSTS_PER_PAGE

@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
@app.route('/index/<int:page>', methods=['GET', 'POST'])
@login_required
def index(page=1):
	user = current_user
	
	form = PostForm()
	if form.validate_on_submit():
		post = Post(body=form.post.data, timestamp=datetime.utcnow(), author=user)
		db.session.add(post)
		db.session.commit()
		flash('Your post is now live!')
		return redirect(url_for('index'))
	
	posts = current_user.followed_posts().paginate(page, POSTS_PER_PAGE, False)
 
	return render_template('index.html',title='Home', user=user, posts=posts, form=form)
	
@app.route('/login', methods=['GET', 'POST'])
def login():
	if current_user.is_authenticated:
		flash('User Already Logged in')
	form = LoginForm()
	if form.validate_on_submit():
		user, authenticated = User.authenticate(form.login.data, form.password.data)
		
		if user:
			if authenticated:
				
				login_user(user, remember=form.remember_me.data)
				flash('login successful')
				return redirect('/index')
		else:
			flash('Username does not exist')
			return redirect('/index')
		
	return render_template('login.html', title='Sign In', form=form)
	
@app.route('/logout')
def logout():
	logout_user()
	flash('You have logged out')
	return redirect(url_for('index'))
	
@app.route('/signup', methods=['GET', 'POST'])
def signup():
	if current_user.is_authenticated:
		flash('User Already Registered')
		
	form = SignupForm()
	
	if form.validate_on_submit():
		if User.is_user_name_taken(form.nickname.data):
			flash('This username is already taken!')
			return redirect(url_for('signup'))
		if User.is_email_taken(form.email.data):
			flash('This email is already taken!')
			return redirect(url_for('signup'))
			
		try:
			user = User()
			form.populate_obj(user)
			
			db.session.add(user)
			db.session.commit()
			
		except Exception as e:
			flash('Error registering user!')
			return redirect(url_for('signup'))
		
		#follow self
		db.session.add(user.follow(user))
		db.session.commit()
		
		#create blank avatar
		shutil.copy2('app/static/avatars/blank.jpg', ('app/static/avatars/'+str(user.id)+'.jpg'))
		
		#log in new user
		login_user(user)
		flash('You successfully signed up!')
		
	return render_template('signup.html', title='Sign Up', form=form)

@app.route('/user/<nickname>')
@app.route('/user/<nickname>/<int:page>')
@login_required
def user(nickname, page=1):
	user = User.query.filter_by(nickname=nickname).first()
	if user == None:
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
	posts = user.posts.paginate(page, POSTS_PER_PAGE, False)
	
	return render_template('user.html', user=user, posts=posts)
	
@app.before_request
def before_request():
	if current_user.is_authenticated:
		current_user.last_seen = datetime.utcnow()
		db.session.add(current_user)
		db.session.commit()

def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
	
@app.route('/edit', methods=['GET', 'POST'])
@login_required
def edit():
	form = EditForm()
	if form.validate_on_submit():
		if form.nickname.data != current_user.nickname:
			if User.is_user_name_taken(form.nickname.data):
				flash('Username is already taken!')
				return redirect(url_for('edit'))
			else:
				current_user.nickname = form.nickname.data
		current_user.about_me = form.about_me.data
				
		f = request.files['file']
		if f.filename != '':
			f.filename = str(current_user.id)+'.jpg'
			filename = secure_filename(f.filename)
			f.save(os.path.join('app/static/avatars', filename))
		
		db.session.add(current_user)
		db.session.commit()
		flash('Your changes have been saved.')
		return redirect(url_for('edit'))
	else:
		form.nickname.data = current_user.nickname
		form.about_me.data = current_user.about_me
	
	return render_template('edit.html', form=form)

#static url cache buster	
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                     endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)
	
@app.route('/follow/<nickname>')
@login_required
def follow(nickname):
	user= User.query.filter_by(nickname=nickname).first()
	if user is None:
		flash('User %s not found' % nickname)
		return redirect(url_for('index'))
	if user == current_user:
		flash('You can\'t follow yourself!')
		return redirect(url_for('user', nickname=nickname))
	u = current_user.follow(user)
	if u is None:
		flash('Cannot follow '+ nickname )
		return redirect(url_for('user', nickname=nickname))
	db.session.add(u)
	db.session.commit()
	flash('You are now following ' + nickname )
	return redirect(url_for('user', nickname=nickname))
	
@app.route('/unfollow/<nickname>')
@login_required
def unfollow(nickname):
	user = User.query.filter_by(nickname=nickname).first()
	if user is None:
		flash('User %s not found' % nickname)
		return redirect(url_for('index'))
	if user == current_user:
		flash('You can\'t unfollow yourself!')
		return redirect(url_for('user', nickname=nickname))
	u = current_user.unfollow(user)
	if u is None:
		flash('Cannot unfollow ' + nickname )
		return redirect(url_for('user', nickname=nickname))
	db.session.add(u)
	db.session.commit()
	flash('You have stopped following ' + nickname)
	return redirect(url_for('user', nickname=nickname))