import os

WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

POSTS_PER_PAGE = 3

UPLOAD_FOLDER = 'app/static/avatars/'

LANGUAGES = {
	'en': 'English',
	'es': 'Espanol'
}