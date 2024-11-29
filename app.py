from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from models import db, Trip, MenuItem , Restaurant
import json
from flask_jwt_extended import decode_token

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fikaso.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'secret_key'  # Change ceci pour la production
app.config["JWT_IDENTITY_CLAIM"] = "sub"


# Initialisation de la base de données, JWT et Flask-Migrate
db = SQLAlchemy(app)
jwt = JWTManager(app)
migrate = Migrate(app, db)

# Modèles de la base de données

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255))

class Restaurant(db.Model):
    __tablename__ = 'restaurant'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    address = db.Column(db.String, nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # ID du propriétaire
    owner = db.relationship('User', backref=db.backref('restaurants', lazy=True))

    # Relation avec les plats
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy=True)


class MenuItem(db.Model):
    __tablename__ = 'menu_item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)  # Nom du plat
    price = db.Column(db.Float, nullable=False)  # Prix du plat
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)  # ID du restaurant



class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    delivery_address = db.Column(db.String, nullable=False)
    items = db.Column(db.Text, nullable=False)  # Stocké comme JSON string
    total_price = db.Column(db.Float, nullable=False)

    def get_items(self):
        return json.loads(self.items)  # Convertir la chaîne JSON en liste Python



# Crée les tables si elles n'existent pas déjà
with app.app_context():
    db.create_all()

# Routes de l'application

# Enregistrement d'un utilisateur
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']

    if User.query.filter_by(username=username).first():
        return jsonify({'message': 'User already exists'}), 400

    new_user = User(username=username, password=password)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User registered successfully'}), 201

# Connexion de l'utilisateur
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username).first()
    if user and user.password == password:
        access_token = create_access_token(identity=str(user.id))
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/user/<int:user_id>', methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        return jsonify({"error": "User not found"}), 404
    return jsonify({"id": user.id, "username": user.username})


#Cette route permet à un utilisateur authentifié d'ajouter un restaurant.
@app.route('/create_restaurant', methods=['POST'])
def create_restaurant():
    data = request.get_json()

    try:
        # Création du restaurant
        restaurant = Restaurant(
            name=data['name'],
            address=data['address'],
            owner_id=data['owner_id'],
        )

        # Ajout des plats au restaurant (si spécifié dans la requête)
        if 'menu_items' in data:
            for item in data['menu_items']:
                menu_item = MenuItem(
                    name=item['name'],
                    price=item['price'],
                    restaurant_id=restaurant.id  # Lier le plat au restaurant
                )
                restaurant.menu_items.append(menu_item)  # Ajouter le plat à la relation

        db.session.add(restaurant)
        db.session.commit()

        return jsonify({"message": "Restaurant créé avec succès avec les plats."}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



#obtenir les détails d'un restaurant spécifique
@app.route('/create_restaurant/<int:restaurant_id>', methods=['GET'])
def get_restaurant_details(restaurant_id):
    try:
        # Rechercher le restaurant par son ID
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        # Préparer les détails du restaurant et des plats associés
        restaurant_details = {
            "id": restaurant.id,
            "name": restaurant.name,
            "address": restaurant.address,
            "owner_id": restaurant.owner_id,
            "menu_items": [
                {"id": item.id, "name": item.name, "price": item.price}
                for item in restaurant.menu_items
            ]
        }

        return jsonify(restaurant_details), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#Modification des informations d’un restaurant
@app.route('/create_restaurant/<int:restaurant_id>', methods=['PUT'])
def update_restaurant(restaurant_id):
    try:
        # Récupérer les données de la requête JSON
        data = request.get_json()

        # Trouver le restaurant par son ID
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        # Mettre à jour les champs du restaurant
        restaurant.name = data.get('name', restaurant.name)
        restaurant.address = data.get('address', restaurant.address)
        restaurant.owner_id = data.get('owner_id', restaurant.owner_id)

        # Commit des changements dans la base de données
        db.session.commit()

        return jsonify({"message": "Restaurant updated successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#Supprimer tous les plats d'un restaurant
@app.route('/create_restaurant/<int:restaurant_id>/menu', methods=['DELETE'])
def delete_all_menu_items(restaurant_id):
    try:
        # Supprimer tous les plats du restaurant
        MenuItem.query.filter_by(restaurant_id=restaurant_id).delete()
        db.session.commit()

        return jsonify({"message": "All menu items deleted successfully"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500



#Cette route permet d'ajouter un repas à un restaurant.
@app.route('/create_restaurant/<int:restaurant_id>/meals', methods=['POST'])
def add_dish(restaurant_id):
    data = request.get_json()
    try:
        # Trouver le restaurant correspondant
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        # Créer un nouveau plat
        new_dish = MenuItem(
            name=data['name'],
            price=data['price'],
            restaurant_id=restaurant_id
        )

        db.session.add(new_dish)
        db.session.commit()

        return jsonify({"message": "Dish added successfully", "dish": {"name": new_dish.name, "price": new_dish.price}}), 201
    except KeyError as e:
        return jsonify({"error": f"Missing parameter: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#Cette route permet de lister tous les repas d'un restaurant.
@app.route('/restaurant/<int:restaurant_id>/dishes', methods=['GET'])
def get_dishes(restaurant_id):
    try:
        # Trouver le restaurant correspondant
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({"error": "Restaurant not found"}), 404

        # Récupérer les plats associés
        dishes = [{"id": dish.id, "name": dish.name, "price": dish.price} for dish in restaurant.menu_items]
        return jsonify({"restaurant": restaurant.name, "dishes": dishes}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


#faire une commande
@app.route('/orders', methods=['POST'])
def create_order_manual_jwt():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"message": "Authorization header is missing"}), 401
    if not auth_header.startswith("Bearer "):
        return jsonify({"message": "Authorization header must start with 'Bearer '"}), 401

    token = auth_header.split(" ")[1]  # Extraire le jeton
    try:
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub")  # Récupérer l'ID utilisateur à partir du JWT

        # Vérifier que user_id est une chaîne
        if not isinstance(user_id, str):
            return jsonify({"message": "Invalid token: 'sub' must be a string"}), 401

        print("Utilisateur connecté :", user_id)
    except Exception as e:
        return jsonify({"message": f"Token decode error: {str(e)}"}), 401

    return jsonify({"message": "Request processed successfully", "user_id": user_id}), 200

@app.route('/debug_jwt', methods=['GET'])
def debug_jwt():
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return jsonify({"message": "Authorization header is missing"}), 401
    if not auth_header.startswith("Bearer "):
        return jsonify({"message": "Authorization header must start with 'Bearer '"}), 401

    token = auth_header.split(" ")[1]
    try:
        decoded_token = decode_token(token)
        return jsonify({"decoded_token": decoded_token}), 200
    except Exception as e:
        return jsonify({"message": f"Token decode error: {str(e)}"}), 401

#Lister les Commandes d'un Utilisateur
@app.route('/orders', methods=['GET'])
@jwt_required()
def list_orders():
    current_user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=current_user_id).all()

    order_list = [
        {
            "id": order.id,
            "restaurant_id": order.restaurant_id,
            "delivery_address": order.delivery_address,
            "items": order.items,
            "total_price": order.total_price,
            "status": order.status,
            "created_at": order.created_at,
        }
        for order in orders
    ]
    return jsonify(order_list), 200

#Mettre à Jour l'État d'une Commande (Pour Admin ou Utilisateur)
@app.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    current_user_id = get_jwt_identity()
    data = request.get_json()
    new_status = data.get('status')

    if not new_status:
        return jsonify({"message": "Status is required"}), 400

    # Vérification de la commande
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404

    # Mise à jour de l'état de la commande
    try:
        order.status = new_status
        db.session.commit()
        return jsonify({"message": "Order status updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500

#Route pour annuler une commande
@app.route('/orders/<int:id>/cancel', methods=['PUT'])
def cancel_order(id):
    order = Order.query.get(id)

    if not order:
        return jsonify({"msg": "Order not found"}), 404

    # Vérifie si la commande est déjà annulée
    if order.status == 'cancelled':
        return jsonify({"msg": "Order is already cancelled"}), 400

    # Annuler la commande
    order.status = 'cancelled'
    db.session.commit()  # Enregistrer les changements dans la base de données
    return jsonify({"msg": "Order has been cancelled", "order_id": order.id}), 200

#Ajoute une route pour mettre à jour l'adresse de l'utilisateur
@app.route('/users/address', methods=['PUT'])
@jwt_required()
def update_address():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    latitude = data.get('latitude')
    longitude = data.get('longitude')
    address = data.get('address')  # Adresse optionnelle générée sur le front-end

    if not all([latitude, longitude]):
        return jsonify({"message": "Latitude and longitude are required"}), 400

    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Mettre à jour l'adresse de l'utilisateur
    user.address = address
    try:
        db.session.commit()
        return jsonify({"message": "Address updated successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500

#Les routes pour gérer les trajets (demander un trajet, assigner un conducteur, etc.)
@app.route('/request_trip', methods=['POST'])
def request_trip():
    data = request.get_json()
    origin = data.get('origin')
    destination = data.get('destination')
    user_id = data.get('user_id')

    new_trip = Trip(user_id=user_id, origin=origin, destination=destination)
    db.session.add(new_trip)
    db.session.commit()

    return jsonify({"msg": "Trip requested", "trip_id": new_trip.id}), 201


#Route pour assigner un conducteur à un trajet
@app.route('/assign_driver/<int:trip_id>', methods=['PUT'])
def assign_driver(trip_id):
    data = request.get_json()
    driver_id = data.get('driver_id')

    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({"msg": "Trip not found"}), 404

    trip.driver_id = driver_id
    trip.status = 'in_progress'
    db.session.commit()

    return jsonify({"msg": "Driver assigned", "trip_id": trip.id, "status": trip.status})

#Route pour mettre à jour l'état du trajet
@app.route('/update_trip_status/<int:trip_id>', methods=['PUT'])
def update_trip_status(trip_id):
    data = request.get_json()
    status = data.get('status')

    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({"msg": "Trip not found"}), 404

    trip.status = status
    db.session.commit()

    return jsonify({"msg": "Trip status updated", "trip_id": trip.id, "status": trip.status})


# Lancer l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
