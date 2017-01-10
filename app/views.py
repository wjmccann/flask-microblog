from flask import render_template, flash, redirect, session, url_for, request, g
from app import app, db
from .forms import LoginForm, SignupForm, EditForm
from flask_login import login_required, login_user, current_user, logout_user, confirm_login, login_fresh
from .models import User
from datetime import datetime
from werkzeug.utils import secure_filename
import os

@app.route('/')
@app.route('/index')
@login_required
def index():
	user = current_user
	posts = [  # fake array of posts
        { 
            'author': {'nickname': 'John'}, 
            'body': 'Beautiful day in Portland!' 
        },
        { 
            'author': {'nickname': 'Susan'}, 
            'body': 'The Avengers movie was so cool!' 
        }
    ]
	return render_template('index.html',title='Home', user=user, posts=posts)
	
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
			
		#log in new user
		login_user(user)
		flash('You successfully signed up!')
		
	return render_template('signup.html', title='Sign Up', form=form)

@app.route('/user/<nickname>')
@login_required
def user(nickname):
	user = User.query.filter_by(nickname=nickname).first()
	if user == None:
		flash('User %s not found.' % nickname)
		return redirect(url_for('index'))
	posts = [ 
		{'author': user, 'body': 'Test post #1'},
		{'author': user, 'body': 'Test post #2'}
	]
	avatar = str(user.id)
	return render_template('user.html', user=user, posts=posts, avatar=avatar)
	
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
			f.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
		
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
	