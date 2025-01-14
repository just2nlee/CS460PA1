######################################
# author ben lawson <balawson@bu.edu>
# Edited by: Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for
from flaskext.mysql import MySQL
import flask_login

#for image uploading
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'NOcap122020!'
app.config['MYSQL_DATABASE_DB'] = 'photoshare'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	supressText = request.args.get('supress') != 'False'
	return render_template('register.html', supress=supressText)

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('firstName')
		last_name=request.form.get('lastName')
		date_of_birth=request.form.get('DOB')
		gender=request.form.get('gender')
		hometown=request.form.get('hometown')
		
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, date_of_birth, gender, hometown) VALUES ('{0}', '{1}', '{2}', '{3}','{4}', '{5}', '{6}')".format(email, password, first_name, last_name, date_of_birth, gender, hometown)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("email not unique")
		return flask.redirect(flask.url_for('register', supress=False))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id  FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		album = request.form.get('albums')
		photo_data =imgfile.read()
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id) VALUES (%s, %s, %s, %s )''', (photo_data, uid, caption, album))
		conn.commit()
		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		cursor = conn.cursor()
		cursor.execute('''SELECT album_id, album_name FROM Albums WHERE user_id=%s''', (uid))
		albums = cursor.fetchall()
		return render_template('upload.html', albums=albums)
#end photo uploading code

@app.route('/create_album', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_name=request.form.get('album-name')
		cursor = conn.cursor()
		cursor.execute('''INSERT INTO Albums (album_name, user_id) VALUES (%s, %s)''', (album_name, uid))
		conn.commit()
		return  flask.redirect(flask.url_for("create_album"))
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		cursor = conn.cursor()
		cursor.execute('''SELECT album_name FROM Albums WHERE user_id=%s''', (uid))
		albums = cursor.fetchall()
		return render_template('createalbum.html', albums=albums)

@app.route("/friends", methods=['GET', 'POST'])
def friends():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		friend = getUserIdFromEmail(request.form.get('friend-email'))
		if notFriends(uid, friend):
			cursor = conn.cursor()
			cursor.execute('''INSERT INTO Friends (userID1, userID2) VALUES (%s, %s)''',(uid, friend))
			conn.commit()
			return flask.redirect(flask.url_for("friends"))
		else:
			return flask.redirect(flask.url_for("friends", error='True'))
	else:
		error = request.args.get('error') == 'True'
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor = conn.cursor()
		cursor.execute('''SELECT first_name, last_name, email FROM Friends INNER JOIN Users ON userID2=user_id WHERE userID1=%s
''', (uid))
		friends = cursor.fetchall()
		print(friends)
		return render_template('friends.html', error=error, friends=friends)

def notFriends(userID1, userID2):
	cursor = conn.cursor()
	cursor.execute('''SELECT * FROM Friends WHERE userID1=%s AND userID2=%s''',(userID1, userID2))
	if len(cursor.fetchall()) == 0:
		return True
	return False

@app.route('/galary', methods=['GET'])
def galary():
	cursor = conn.cursor()
	cursor.execute('''SELECT album_id, album_name FROM Albums''')
	albums = cursor.fetchall()
	print(albums)
	return render_template('galary.html', albums=albums, base64=base64)

@app.route('/album/<album_id>', methods=['GET'])
def album(album_id):
	cursor = conn.cursor()
	cursor.execute('''SELECT imgdata,caption FROM Pictures WHERE album_id=%s''', (album_id))
	photos = cursor.fetchall()
	return render_template('view_album.html', photos=photos, base64=base64)
	
@app.route('/user_albums', methods=['GET', 'POST'])
@flask_login.login_required
def user_albums():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'POST':
		album_id = request.form.get("albums")
		print(album_id)
		cursor = conn.cursor()
		cursor.execute('''DELETE FROM Albums WHERE album_id=%s''', (album_id))
		return flask.redirect(flask.url_for('user_albums'))
	else:
		cursor = conn.cursor()
		cursor.execute('''SELECT album_id, album_name FROM Albums WHERE user_id=%s''', (uid))
		albums = cursor.fetchall()
		return render_template('user_albums.html', albums=albums)

@app.route('/user_albums/<album_id>', methods=['GET', 'DELETE'])
@flask_login.login_required
def manage_user_album(album_id): 
	uid = getUserIdFromEmail(flask_login.current_user.id)
	if request.method == 'DELETE':
		return
	else:
		cursor = conn.cursor()
		cursor.execute('''SELECT imgdata,caption FROM Pictures WHERE album_id=%s''', (album_id))
		photos = cursor.fetchall()
	return render_template('user_album.html', photos=photos,  base64=base64)

#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
