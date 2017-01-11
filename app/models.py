from app import db, login_manager, app
from werkzeug import generate_password_hash, check_password_hash
from flask_login import UserMixin

followers = db.Table('followers',
	db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
	db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)

class User(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	nickname = db.Column(db.String(64), index=True, unique=True)
	email = db.Column(db.String(120), index=True, unique=True)
	posts = db.relationship('Post', backref='author', lazy='dynamic')
	about_me = db.Column(db.String(140))
	last_seen = db.Column(db.DateTime)
	followed = db.relationship('User',
								secondary=followers,
								primaryjoin=(followers.c.follower_id == id),
								secondaryjoin=(followers.c.followed_id == id),
								backref=db.backref('followers', lazy='dynamic'),
								lazy='dynamic')	
	
	_password = db.Column('password', db.String(64))
	
	def _get_password(self):
		return self._password
		
	def _set_password(self, password):
		self._password = generate_password_hash(password)
		
	password = db.synonym('_password', descriptor=property(_get_password, _set_password))
	
	def check_password(self, password):
		if self.password is None:
			return False
		return check_password_hash(self.password, password)
	
	def __repr__(self):
		return '<User %r>' % (self.nickname)
		
	@classmethod
	def authenticate(cls, nickname, password):
		user = User.query.filter(db.or_(User.nickname == nickname)).first()
		
		if user:
			authenticated = user.check_password(password)
		else: 
			authenticated = False
		return user, authenticated
		
	@classmethod
	def is_user_name_taken(cls, nickname):
		return db.session.query(db.exists().where(User.nickname==nickname)).scalar()
		
	@classmethod
	def is_email_taken(cls, email):
		return db.session.query(db.exists().where(User.email==email)).scalar()
		
	@login_manager.user_loader
	def load_user(id):
		return User.query.get(id)
	
	def follow(self, user):
		if not self.is_following(user):
			self.followed.append(user)
			return self
			
	def unfollow(self, user):
		if self.is_following(user):
			self.followed.remove(user)
			return self
			
	def is_following(self, user):
		return self.followed.filter(followers.c.followed_id == user.id).count() > 0
		
	def followed_posts(self):
		return Post.query.join(followers, (followers.c.followed_id == Post.user_id)).filter(followers.c.follower_id == self.id).order_by(Post.timestamp.desc())
	
class Post(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	body = db.Column(db.String(140))
	timestamp = db.Column(db.DateTime)
	user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
	
	def __repr__(self):
		return '<Post %r>' % (self.body)
		
