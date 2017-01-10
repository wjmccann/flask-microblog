from flask_wtf import FlaskForm
from wtforms import (BooleanField, TextField, HiddenField, PasswordField, DateTimeField, validators, IntegerField, SubmitField, TextAreaField)
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
	login = TextField('user_name', [validators.Required()])
	password = PasswordField('password', [validators.Required()])
	remember_me = BooleanField('remember_me', default = False)
	
class SignupForm(FlaskForm):
	nickname = TextField('user_name', [validators.Required()])
	email = TextField('email', [validators.Required(), validators.Email()])
	password = PasswordField('New Password', [validators.Required()])
	confirm = PasswordField('Repeat Password', [validators.Required(), validators.EqualTo('password', message='Passwords must match')])
	
class EditForm(FlaskForm):
	nickname = TextField('nickname', validators=[DataRequired()])
	about_me = TextAreaField('about_me', validators=[Length(min=0, max=140)])