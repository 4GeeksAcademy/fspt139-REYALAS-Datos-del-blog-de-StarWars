"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Planet, Character, FavoritePlanet, FavoriteCharacter

app = Flask(__name__)
app.url_map.strict_slashes = False

db_url = os.getenv("DATABASE_URL")
if db_url is not None:
    app.config['SQLALCHEMY_DATABASE_URI'] = db_url.replace("postgres://", "postgresql://")
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/test.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)

@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

@app.route('/')
def sitemap():
    return generate_sitemap(app)

# --- PEOPLE (Character) ---
@app.route('/people', methods=['GET'])
def get_people():
    return jsonify([c.serialize() for c in Character.query.all()]), 200

@app.route('/people/<int:people_id>', methods=['GET'])
def get_one_people(people_id):
    c = Character.query.get(people_id)
    if not c:
        return jsonify({"msg": "Not found"}), 404
    return jsonify(c.serialize()), 200

# --- PLANETS ---
@app.route('/planets', methods=['GET'])
def get_planets():
    return jsonify([p.serialize() for p in Planet.query.all()]), 200

@app.route('/planets/<int:planet_id>', methods=['GET'])
def get_one_planet(planet_id):
    p = Planet.query.get(planet_id)
    if not p:
        return jsonify({"msg": "Not found"}), 404
    return jsonify(p.serialize()), 200

# --- USERS ---
@app.route('/users', methods=['GET'])
def get_users():
    return jsonify([u.serialize() for u in User.query.all()]), 200

@app.route('/users/favorites', methods=['GET'])
def get_user_favorites():
    user_id = 1  # usuario actual (sin auth)
    fav_people = FavoriteCharacter.query.filter_by(user_id=user_id).all()
    fav_planets = FavoritePlanet.query.filter_by(user_id=user_id).all()
    return jsonify({
        "favorite_characters": [f.serialize() for f in fav_people],
        "favorite_planets": [f.serialize() for f in fav_planets]
    }), 200

def _get_user_id():
    data = request.get_json(silent=True)
    if data and "user_id" in data:
        return data["user_id"]
    return 1

# --- FAVORITES POST ---
@app.route('/favorite/planet/<int:planet_id>', methods=['POST'])
def add_fav_planet(planet_id):
    user_id = _get_user_id()
    if not Planet.query.get(planet_id):
        return jsonify({"msg": "Planet not found"}), 404
    fav = FavoritePlanet(user_id=user_id, planet_id=planet_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.serialize()), 200

@app.route('/favorite/people/<int:people_id>', methods=['POST'])
def add_fav_people(people_id):
    user_id = _get_user_id()
    if not Character.query.get(people_id):
        return jsonify({"msg": "Character not found"}), 404
    fav = FavoriteCharacter(user_id=user_id, character_id=people_id)
    db.session.add(fav)
    db.session.commit()
    return jsonify(fav.serialize()), 200

# --- FAVORITES DELETE ---
@app.route('/favorite/planet/<int:planet_id>', methods=['DELETE'])
def del_fav_planet(planet_id):
    user_id = _get_user_id()
    fav = FavoritePlanet.query.filter_by(user_id=user_id, planet_id=planet_id).first()
    if not fav:
        return jsonify({"msg": "Not found"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Deleted"}), 200

@app.route('/favorite/people/<int:people_id>', methods=['DELETE'])
def del_fav_people(people_id):
    user_id = _get_user_id()
    fav = FavoriteCharacter.query.filter_by(user_id=user_id, character_id=people_id).first()
    if not fav:
        return jsonify({"msg": "Not found"}), 404
    db.session.delete(fav)
    db.session.commit()
    return jsonify({"msg": "Deleted"}), 200

if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)