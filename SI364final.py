## SI364 final project

#######################
## IMPORT STATEMENTS ##
#######################
import os
import requests
import json
from flask import Flask, render_template, session, redirect, request, url_for, flash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, IntegerField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError, RadioField, SelectField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, MigrateCommand
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import yelp_api

###############
## APP SETUP ##
###############
app = Flask(__name__)
app.debug = True
app.use_reloader = True

#######################
## APP CONFIGURATION ##
#######################
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:siyi1126@localhost/SI364projectplantayzheng'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


client_id = yelp_api.client_id
api_key = yelp_api.api_key

####################
## MORE APP SETUP ##
####################
manager = Manager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
manager.add_command('db', MigrateCommand)

#login configuration
login_manager = LoginManager()
login_manager.init_app(app) 
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'



######################
## HELPER FUNCTIONS ####################################################################
######################

def get_or_create_restaurant(name, location):
    restaurants = rRestaurant.query.filter_by(name = name).first()
    if restaurants:
        return restaurants
    else:
        restaurants = restaurant(name = name, location = location)
        db.session.add(restaurants)
        db.session.commit()
        return restaurants

def get_restaurant_data(name):
	base_url = 'https://api.yelp.com/v3/businesses/search'
	params = {'api_key': api_key, 'term': restaurant, 'location': location}
	headers = {'Authorization': 'Bearer %s' % api_key}
	data = requests.get(baseurl, headers = headers, params = params)
	json_data = json.loads(data.text)
	return json_data


def get_restaurant_by_id(id):
	rest = Restaurant.query.filter_by(id=id).first()
	return rest

def get_or_create_itinerary(name, user, restaurant_list =[]):
	itinerary = Itinerary.query.filter_by(name = name, user = user.id).first()
	if itinerary:
		return itinerary
	else:
		itinerary = Itinerary(name = name, user = user.id)
		for x in list:
			itinerary.restaurants.append(x)
		db.session.add(itinerary)
		db.session.commit()

############
## MODELS ##
############

## Association Tables ##

#Restaurants and Reviews
#M:M
restaurants_and_reviews = db.Table('restaurants_and_reviews', db.Column('restaurant', db.Integer, db.ForeignKey('restaurant.id')), db.Column('restaurant_reviews', db.Integer, db.ForeignKey('restaurant_reviews.id')))

#Restaurant and Itinerary, bookmarked locations of places the user wants to go to, or has been to
#M:M
bookmark = db.Table('bookmark', db.Column('restaurant', db.Integer, db.ForeignKey('restaurant.id')), db.Column('itinerary', db.Integer, db.ForeignKey('itinerary.id')))

#########################

def form():
	pass

class User(UserMixin, db.Model):
	__tablename__ = "users"
	id = db.Column(db.Integer, primary_key=True)
	username = db.Column(db.String(255), unique=True, index=True)
	email = db.Column(db.String(64), unique=True, index=True)
	password_hash = db.Column(db.String(128))
	reviews = db.relationship('Review', backref = 'users')

	#from HW4#
	@property
	def password(self):
		raise AttributeError('password is not a readable attribute')

	@password.setter
	def password(self, password):
		self.password_hash = generate_password_hash(password)

	def verify_password(self, password):
		return check_password_hash(self.password_hash, password)

def load_user(user_id):
	return User.query.get(int(user_id))

class Restaurant(db.Model):
	__tablename__ = "restaurant"
	id = db.Column(db.Integer, primary_key = True)
	restuarant = db.Column(db.String, unique = True)
	location = db.Column(db.String)
	reviews = db.relationship('Review', backref = 'restaurant')

	def __repr__(self):
		return 'Restaurant Name: {}'.format(self.restaurant)

class Review(db.Model):
	__tablename__ = "restaurant_reviews"
	id = db.Column(db.Integer, primary_key = True)
	stars = db.Column(db.Integer)
	review = db.Column(db.String(5000))
	rest_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'))

class Itinerary(db.Model):
	__tablename__ = "itinerary"
	id = db.Column(db.Integer, primary_key = True)
	name = db.Column(db.String(128))
	user = db.Column(db.Integer, db.ForeignKey('users.id'))
	restaurants = db.relationship('restaurant', secondary = bookmark, backref = db.backref('itinerary', lazy = 'dynamic'), lazy = 'dynamic')

###########
## FORMS ##
###########

#from HW4#
class CreateAccountForm(FlaskForm):
	email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
	username = StringField('Username:',validators=[Required(),Length(1,64)])
	password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match, please try again.")])
	password2 = PasswordField("Confirm Password:",validators=[Required()])
	submit = SubmitField('Register User')


	def validate_email(self,field):
		if User.query.filter_by(email=field.data).first():
			raise ValidationError('This email has been registered already.')

	def validate_username(self,field):
		if User.query.filter_by(username=field.data).first():
			raise ValidationError('Sorry, that username already exists.')

class LoginForm(FlaskForm):
	email = StringField('Email', validators=[Required(), Length(1,64), Email()])
	password = PasswordField('Password', validators=[Required()])
	remember_me = BooleanField('Keep me logged in!')
	submit = SubmitField('Log In')

###############

class RestaurantForm(FlaskForm):
	name = StringField('Enter the name of a restaurant to see what people think!', validators = [Required()])
	location = StringField('What location would you like to search?')
	submit = SubmitField()

#list of places user wants to go eat for a location they want to visit/have visited
class ItineraryForm(FlaskForm):
	list_name = StringField('Name your itinerary!', validators = [Required()])
	restaurant_picks = SelectMultipleField('Places to visit include:', coerce=int)
	submit = SubmitField('Create itinerary!')

#if the user has been to the location, they can write down what they thought of the place
class ReviewForm(FlaskForm):
	restaurant = StringField('Restaurant name: ', validators = [Required()])
	stars = IntegerField('What would you rate this place overall out of 5 stars?', validators = [Required()])
	food = StringField('How good was your food? Please rate it out of 5.', validators = [Required()])
	price = StringField('Do you think the food was worth the price? Please rate it out of 5.', validators = [Required()])
	rest_review = StringField('Leave your thoughts here!', validators = [Required()])
	submit = SubmitField()

	def validate_stars(form, field):
		if len(field.data) > 1:
			raise ValidationError('Please rate out of full numbers, no decimals!')

#CRUD
class UpdateButtonForm(FlaskForm):
	update = SubmitField('Update')

class DeleteButtonForm(FlaskForm):
	delete = SubmitField('Delete')


####################
## VIEW FUNCTIONS ##############################################################################
####################

 #CreateAccount page to create an account. 
#When the form is submitted, a user is added to the database and users should be redirected to the login page.
@app.route('/register', methods=["GET", "POST"])
def register():
	form = RegistrationForm()
	if form.validate_on_submit():
		user = User(email=form.email.data,username=form.username.data,password=form.password.data)
		db.session.add(user)
		db.session.commit()
		flash('You have successfully created an account.')
		return redirect(url_for('login'))
	return render_template('register.html',form=form)

#Should render a login page.
# asking the user to log into their account | then they will be redirected to the home page
@app.route('/login', methods=["GET", "POST"])
def login():
	form = LoginForm()
	if form.validate_on_submit():
		user = User.query.filter_by(email=form.email.data).first()
		if user is not None and user.verify_password(form.password.data):
			login_user(user, form.remember_me.data)
			return redirect(request.args.get('next') or url_for('base'))
		flash('Invalid username or password.')
	return render_template('login.html',form=form)

#This allows the user to logout, and will return them to the home page
@app.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out')
	return redirect(url_for('base'))


@app.route('/secret')
@login_required
def secret():
	return "Only authenticated users can do this! Try to log in or contact the site admin."

############################################################

## home page, first thing seen
@app.route('/') 
def base():
	return render_template('base.html', form=form)

#renders the restaurant form, where users can input a restaurant name
@app.route('/restaurant_search') 
def restaurant_search():
	form = restaurant_Form()
	return render_template('restaurant_search.html', form = form)

@app.route('/restaurant_data', methods = ['GET', 'POST']) 
def restaurant_data():
	name = form.name.data
	restaurant = form.restaurant.data
	location = form.location.data
    
	same_rest = Restaurant.query.filter_by(restaurant = restaurant, location = location).first()
	if same_rest:
		rest = Restaurant.query.filter_by(restaurant = restaurant, location = location)
	else:
		rest = Restaurant(restaurant = restaurant, location = location)
		db.session.add(rest)
		db.session.commit()
	restaurantID = json_data['businesses'][0]['id']
	yelp_review = 'https://api.yelp.com/v3/businesses/'
	yelp_review2 = yelp_review + restaurantID + '/reviews'
	getdata = requests.get(yelp_review2, headers = headers)
	rev_data = json.loads(getdata.text)
	return render_template('base.html', name = name, restuanrat = restaurant, location = location, form=form)

#shows all the previously searched restaurants by the user
@app.route('/searched_restaurants') 
def all_restaurants():
	restaurants = restaurant.query.all()
	return render_template('search_restaurants.html', restaurants = name)

#users can leave a review for a restaurant
@app.route('/restaurant_review') 
def restaurant_review():
	form = restaurant_Review_Form()
	return render_template('restaurant_review.html', form = form)

#users can see all the reviews they have left for restaurants
@app.route('/all_reviews', methods = ['GET', 'POST']) 
def all_reviews():
	form = restaurant_Review_Form()
	if form.validate_on_submit():
		restaurant = form.restaurant.data
		stars = form.stars.data
		review = form.rest_review.data
		restaurant_review = Review.query.filter_by(name = restaurant, stars = stars, review = review).first()
		db.session.add(restaurant_review)
		db.session.commit()
	reviews = Review.query.all()
	all_reviews = []
	for review in reviews:
		tup = (review.name, review.stars, review.review)
		all_reviews.append(tup)
	return render_template('all_reviews.html', all_reviews = all_reviews, form=form)

#users can create a list of restaurants to save based on different locations, etc.
@app.route('/create_itinerary') 
@login_required
def itinerary():
	form = restaurant_Itinerary_Form()
	restaurants = restaurant.query.all()
	choices = [(rest.id, rest.name) for rest in restaurants]
	form.restaurant_picks.choices = choices
	if form.validate_on_submit():
		restaurant_list = []
		for x in form.restaurant_picks.data:
			restaurant = get_restaurant_by_id(x)
			restaurant_list.append(restaurant)
		itinerary = get_or_create_itinerary(form.name.data, current_user, restaurant_list)
		return redirect(url_for('itinerary'))
	return render_template('create_itinerary.html', form = form)


@app.route('/itinerary') 
@login_required
def itinerary():
    itinerarys = Itinerary.query.filter_by(user = user.id).all()
    return render_template('itinerary.html', itinerarys = itinerarys)

@app.route('/delete/<lst>', methods=["GET", "POST"])
def delete(lst):
	delete_lst = Itinerary.query.filter_by(name = name).first()
	if delete_lst:
		db.session.delete(delete_lst)
		flash('Deleted list: {}'.format(delete_lst.name))
	return redirect(url_for('itinerary'))

#####################
## ERROR FUNCTIONS ######################################################################
#####################

@app.errorhandler(404)
def page_not_found(e):
	return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
	return render_template('500.html'), 500

##########################################################################################

if __name__ == '__main__':
	db.create_all()
	manager.run()
	app.run(use_reloader = True, debug = True)
	