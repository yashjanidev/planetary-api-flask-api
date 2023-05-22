from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Float
import os
from flask_marshmallow import Marshmallow
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_mail import Mail, Message

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
# sqlite:///path/to/database.db
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///C:/Users/theya/OneDrive/Desktop/flasklearning/dayone/planets.db'
app.config['JWT_SECRET_KEY'] = 'super_secret'
# app.config['MAIL_SERVER'] = 'smtp.mailtrap.io'
# app.config['MAIL_USERNAME'] = os.environ['MAIL_USERNAME']
# app.config['MAIL_PASSWORD'] = os.environ['MAIL_PASSWORD']
app.config['MAIL_SERVER']='sandbox.smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '5ed30be761bbca'
app.config['MAIL_PASSWORD'] = '9d92388bd4e64c'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False


db = SQLAlchemy(app)
ma = Marshmallow(app)
jwt = JWTManager(app)
mail = Mail(app)
# This is default route


@app.cli.command('db_create')
def db_create():
    db.create_all()
    print("Database created !")


@app.cli.command('db_drop')
def db_drop():
    db.drop_all()
    print("Database Dropped !")


@app.cli.command('db_seed')
def db_seed():
    mercury = Planet(planet_name='Mercury',
                     planet_type='Class D',
                     home_star='Sol',
                     mass=3.258e23,
                     radius=1516,
                     distance=35.98e6)

    venus = Planet(planet_name='Venus',
                   planet_type='Class K',
                   home_star='Sol',
                   mass=4.867e24,
                   radius=3760,
                   distance=67.24e6)

    earth = Planet(planet_name='Earth',
                   planet_type='Class M',
                   home_star='Sol',
                   mass=5.972e24,
                   radius=3959,
                   distance=92.96e6)

    db.session.add(mercury)
    db.session.add(venus)
    db.session.add(earth)

    test_user = User(first_name='William',
                     last_name='Herschel',
                     email='test@test.com',
                     password='password')

    db.session.add(test_user)
    db.session.commit()
    print("Database Seeded!")


@app.route('/')
def index():
    return 'Hello World!'


# This is first page route
@app.route('/first_page')
def first_page():
    return jsonify(message='This is the first page'), 200


# This is Page Not Found Error
@app.route('/not_found')
def not_found():
    return jsonify(message='That resource was not found'), 404


# This is an function which takes parameters and display to web link (Not Recommended)
@app.route('/parameters')
def parameters():
    name = request.args.get('name')
    age = int(request.args.get('age'))

    if (age < 18):
        return jsonify(message=name + ' you are not eligible to vote')
    else:
        return jsonify(message='Congrats ' + name + ' you are eligible to vote')


# This is an function which takes parameters and display to web link in clean way (Recommended)
@app.route('/url_variables/<string:name>/<int:age>')
def url_variables(name: str, age: int):
    if (age < 18):
        return jsonify(message=name + ' you are not eligible to vote')
    else:
        return jsonify(message='Congrats ' + name + ' you are eligible to vote')


@app.route('/planets', methods=['GET'])
def planets():
    planets_list = Planet.query.all()
    # jsonify(data=planets_list)
    result = planets_schema.dump(planets_list)
    return jsonify(result)


@app.route('/register', methods=['POST'])
def register():
    email = request.form['email']
    test = User.query.filter_by(email=email).first()
    if test:
        return jsonify(message='The email is already exists'), 409
    else:
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        password = request.form['password']
        user = User(first_name = first_name, last_name = last_name, password = password)
        db.session.add(user)
        db.session.commit()
        return jsonify(message='User created Successfully'), 201


@app.route('/login', methods=['POST'])
def login():
    if request.is_json:
        email = request.json['email']
        password = request.json['password']
    else:
        email = request.form['email']
        password = request.form['password']

    test = User.query.filter_by(email=email, password=password).first()
    if test:
        access_token = create_access_token(identity=email)
        return jsonify(message='Login succeeded!', access_token=access_token)
    else:
        return jsonify(message="Bad email or password"), 401


@app.route('/get_password/<string:email>', methods=['GET'])
def get_password(email:str):
    user = User.query.filter_by(email=email).first()
    if user:
        msg = Message('Your Planetary API Password is ' + user.password,
                      sender="admin@planetary-api.com",
                      recipients=[email])
        mail.send(msg)
        return jsonify("Password is sent to " + email)
    else:
        return jsonify("Email does not exists!"), 401


@app.route('/planet_details/<int:planet_id>',  methods=['GET'])
def planet_details(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        result = planet_schema.dump(planet)
        return jsonify(result)
    else:
        return jsonify("Planet does not exists!")


@app.route('/add_planet', methods=['POST'])
@jwt_required()
def add_planet():
    planet_name = request.form['planet_name']
    test = Planet.query.filter_by(planet_name=planet_name).first()
    if test:
        return jsonify("The planet already exists!")
    else:
        planet_type = request.form['planet_type']
        home_star = request.form['home_star']
        mass = float(request.form['mass'])
        radius = float(request.form['radius'])
        distance = float(request.form['distance'])
        new_planet = Planet(planet_name=planet_name, planet_type=planet_type, home_star=home_star, mass=mass, radius=radius,
                        distance=distance)
        db.session.add(new_planet)
        db.session.commit()
        return jsonify("New planet added"), 201


@app.route('/update_planet', methods=['PUT'])
@jwt_required()
def update_planet():
    planet_id = int(request.form['planet_id'])
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        planet.planet_name = request.form['planet_name']
        planet.planet_type = request.form['planet_type']
        planet.home_star = request.form['home_star']
        planet.mass = float(request.form['mass'])
        planet.radius = float(request.form['radius'])
        planet.distance = float(request.form['distance'])
        db.session.commit()
        return jsonify("Planet updated")
    else:
        return jsonify("The planet does not exists!")


@app.route('/remove_planet/<int:planet_id>', methods=['DELETE'])
@jwt_required()
def remove_planet(planet_id: int):
    planet = Planet.query.filter_by(planet_id=planet_id).first()
    if planet:
        db.session.delete(planet)
        db.session.commit()
        return jsonify("You deleted a planet"), 202
    else:
        return jsonify("The planet doesn't exists!"), 404


# database models

class User(db.Model):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String, unique=True)
    password = Column(String)


class Planet(db.Model):
    __tablename__ = 'planets'
    planet_id = Column(Integer, primary_key=True)
    planet_name = Column(String)
    planet_type = Column(String)
    home_star = Column(String)
    mass = Column(Float)
    radius = Column(Float)
    distance = Column(Float)


class UserSchema(ma.Schema):
    class Meta:
        fields = ('id', 'first_name', 'last_name', 'email', 'password')


class PlanetSchema(ma.Schema):
    class Meta:
        fields = ('planet_id', 'planet_name', 'planet_type', 'home_star', 'mass', 'radius', 'distance')


user_schema = UserSchema()
users_schema = UserSchema(many=True)


planet_schema = PlanetSchema()
planets_schema = PlanetSchema(many=True)


if __name__ == '__main__':
    app.run(debug=True)