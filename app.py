from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token
from flask_migrate import Migrate
from flask import Flask, request, jsonify
from models import db, Trip, MenuItem , Restaurant
import json
from flask_jwt_extended import decode_token
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

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

class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Autres champs pour les conducteurs


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
    status = db.Column(db.String(50), default="pending", nullable=False)  # Nouveau champ

    def get_items(self):
        return json.loads(self.items)  # Convertir la chaîne JSON en liste Python

class Trip(db.Model):
    __tablename__ = 'trips'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)  # Référence à la table drivers
    start_latitude = db.Column(db.Float, nullable=False)
    start_longitude = db.Column(db.Float, nullable=False)
    end_latitude = db.Column(db.Float, nullable=False)
    end_longitude = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="pending", nullable=False)

    # Relations
    user = db.relationship('User', backref=db.backref('trips', lazy=True))
    driver = db.relationship('Driver', backref='trips')  # Relation avec le modèle Driver







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

    token = auth_header.split(" ")[1]
    try:
        # Décoder le token JWT pour obtenir les informations utilisateur
        decoded_token = decode_token(token)
        user_id = decoded_token.get("sub")

        # Vérifier si user_id est valide
        if not isinstance(user_id, str):
            return jsonify({"message": "Invalid token: 'sub' must be a string"}), 401

        print("Utilisateur connecté :", user_id)
    except Exception as e:
        return jsonify({"message": f"Token decode error: {str(e)}"}), 401

    try:
        # Récupérer les données de la requête
        data = request.get_json()
        restaurant_id = data.get('restaurant_id')
        delivery_address = data.get('delivery_address')
        items = data.get('items')
        total_price = data.get('total_price')

        # Validation des champs
        if not all([restaurant_id, delivery_address, items, total_price]):
            return jsonify({"message": "All fields are required"}), 400

        # Vérifier si le restaurant existe
        restaurant = Restaurant.query.get(restaurant_id)
        if not restaurant:
            return jsonify({"message": "Restaurant not found"}), 404

        # Créer la commande
        new_order = Order(
            user_id=user_id,
            restaurant_id=restaurant_id,
            delivery_address=delivery_address,
            items=json.dumps(items),  # Convertir les items en JSON string
            total_price=total_price
        )
        db.session.add(new_order)
        db.session.commit()

        return jsonify({"message": "Order created successfully", "order_id": new_order.id}), 201
    except Exception as e:
        db.session.rollback()
        print(f"Erreur : {str(e)}")
        return jsonify({"message": "An error occurred while creating the order", "error": str(e)}), 500


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
@app.route('/orders/ongoing', methods=['GET'])
@jwt_required()
def list_ongoing_orders():
    current_user_id = get_jwt_identity()

    try:
        # Filtrer les commandes en fonction de l'utilisateur et du statut
        ongoing_orders = Order.query.filter(
            Order.user_id == current_user_id,
            Order.status.in_(["pending", "in_progress"])
        ).all()

        # Construire la réponse JSON
        orders_list = [
            {
                "id": order.id,
                "restaurant_id": order.restaurant_id,
                "delivery_address": order.delivery_address,
                "items": order.get_items(),
                "total_price": order.total_price,
                "status": order.status
            }
            for order in ongoing_orders
        ]

        return jsonify(orders_list), 200
    except Exception as e:
        print(f"Erreur lors de la récupération des commandes : {str(e)}")
        return jsonify({"message": "An error occurred while fetching ongoing orders", "error": str(e)}), 500
@app.route('/orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_order(order_id):
    current_user_id = get_jwt_identity()

    # Rechercher la commande par son ID
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404

    # Vérifier que l'utilisateur est le propriétaire
    if order.user_id != current_user_id:
        return jsonify({"message": "You are not authorized to view this order"}), 403

    # Retourner les détails de la commande
    return jsonify({
        "id": order.id,
        "restaurant_id": order.restaurant_id,
        "delivery_address": order.delivery_address,
        "items": json.loads(order.items),
        "total_price": order.total_price,
        "status": order.status
    }), 200



#Mettre à Jour l'État d'une Commande (Pour Admin ou Utilisateur)
@app.route('/orders/<int:order_id>', methods=['PUT'])
@jwt_required()
def update_order(order_id):
    current_user_id = get_jwt_identity()

    try:
        # Récupérer les données de la requête
        data = request.get_json()

        # Récupérer la commande
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"message": "Order not found"}), 404

        # Vérifier si l'utilisateur connecté est le propriétaire de la commande
        if order.user_id != current_user_id:
            return jsonify({"message": "You are not authorized to update this order"}), 403

        # Mettre à jour les champs spécifiés
        if 'delivery_address' in data:
            order.delivery_address = data['delivery_address']
        if 'items' in data:
            order.items = json.dumps(data['items'])  # Convertir les items en JSON string
        if 'total_price' in data:
            order.total_price = data['total_price']
        if 'status' in data:
            order.status = data['status']

        # Enregistrer les modifications
        db.session.commit()
        return jsonify({"message": "Order updated successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"An error occurred while updating the order: {str(e)}"}), 500

#Route pour annuler une commande
@app.route('/orders/<int:order_id>/cancel', methods=['PATCH'])
@jwt_required()
def cancel_order(order_id):
    current_user_id = get_jwt_identity()

    try:
        # Récupérer la commande par son ID
        order = Order.query.get(order_id)
        if not order:
            return jsonify({"message": "Order not found"}), 404

        # Vérifier que l'utilisateur connecté est le propriétaire de la commande
        if order.user_id != current_user_id:
            return jsonify({"message": "You are not authorized to cancel this order"}), 403

        # Vérifier si la commande est déjà terminée ou annulée
        if order.status in ["completed", "canceled"]:
            return jsonify({"message": f"Order cannot be canceled as it is already {order.status}"}), 400

        # Mettre à jour le statut de la commande
        order.status = "canceled"

        # Enregistrer les modifications dans la base de données
        db.session.commit()

        return jsonify({"message": "Order has been canceled successfully"}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"An error occurred while canceling the order: {str(e)}"}), 500


#Ajoute une route pour mettre à jour l'adresse de l'utilisateur
class Delivery(db.Model):
    __tablename__ = 'deliveries'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    departure_latitude = db.Column(db.Float, nullable=False)
    departure_longitude = db.Column(db.Float, nullable=False)
    arrival_latitude = db.Column(db.Float, nullable=False)
    arrival_longitude = db.Column(db.Float, nullable=False)
    distance = db.Column(db.Float, nullable=False)

    user = db.relationship('User', backref='deliveries')

    def __repr__(self):
        return f'<Delivery {self.id}>'



@app.route('/users/delivery', methods=['POST'])
@jwt_required()
def create_delivery():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    departure_latitude = data.get('departure_latitude')
    departure_longitude = data.get('departure_longitude')
    arrival_latitude = data.get('arrival_latitude')
    arrival_longitude = data.get('arrival_longitude')

    # Validation des coordonnées GPS
    try:
        departure_latitude = float(departure_latitude)
        departure_longitude = float(departure_longitude)
        arrival_latitude = float(arrival_latitude)
        arrival_longitude = float(arrival_longitude)
    except (TypeError, ValueError):
        return jsonify({"message": "Coordinates must be valid numbers"}), 400

    # Vérification de l'utilisateur
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    # Calculer la distance entre les deux points
    departure_point = (departure_latitude, departure_longitude)
    arrival_point = (arrival_latitude, arrival_longitude)

    try:
        distance = geodesic(departure_point, arrival_point).kilometers
    except Exception as e:
        return jsonify({"message": f"Failed to calculate distance: {str(e)}"}), 500

    # Enregistrer la livraison
    delivery = Delivery(
        user_id=current_user_id,
        departure_latitude=departure_latitude,
        departure_longitude=departure_longitude,
        arrival_latitude=arrival_latitude,
        arrival_longitude=arrival_longitude,
        distance=distance
    )

    try:
        db.session.add(delivery)
        db.session.commit()
        return jsonify({
            "message": "Delivery created successfully",
            "distance": distance,
            "departure": {
                "latitude": departure_latitude,
                "longitude": departure_longitude
            },
            "arrival": {
                "latitude": arrival_latitude,
                "longitude": arrival_longitude
            }
        }), 201
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

#cree un trajet
@app.route('/trips', methods=['POST'])
@jwt_required()
def create_trip():
    """
    Crée un trajet pour un utilisateur authentifié. Un conducteur peut être assigné.
    """
    current_user_id = get_jwt_identity()  # Récupère l'ID de l'utilisateur connecté

    # Récupérer les données envoyées dans la requête
    data = request.get_json()

    start_latitude = data.get('start_latitude')
    start_longitude = data.get('start_longitude')
    end_latitude = data.get('end_latitude')
    end_longitude = data.get('end_longitude')
    driver_id = data.get('driver_id')  # Ce champ est optionnel

    # Vérification des coordonnées
    if not all([start_latitude, start_longitude, end_latitude, end_longitude]):
        return jsonify({"message": "Start and end coordinates are required"}), 400

    # Créer un nouvel objet Trip
    new_trip = Trip(
        user_id=current_user_id,  # L'utilisateur actuel
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        end_latitude=end_latitude,
        end_longitude=end_longitude,
        driver_id=driver_id,  # Optionnel si aucun conducteur n'est assigné
        status="pending"  # Statut initial
    )

    # Ajouter à la base de données
    try:
        db.session.add(new_trip)
        db.session.commit()
        return jsonify({
            "message": "Trip created successfully",
            "trip_id": new_trip.id,
            "status": new_trip.status
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error creating trip: {str(e)}"}), 500


#Lister tous les trajets disponibles
@app.route('/trips', methods=['GET'])
@jwt_required()
def list_trips():
    trips = Trip.query.all()  # Récupérer tous les trajets
    trips_list = [
        {
            "id": trip.id,
            "user_id": trip.user_id,
            "driver_id": trip.driver_id,
            "status": trip.status,
            "delivery_address": trip.delivery_address
        }
        for trip in trips
    ]
    return jsonify(trips_list), 200



#Route pour assigner un conducteur à un trajet
@app.route('/trips/<int:trip_id>/assign_driver', methods=['PUT'])
@jwt_required()
def assign_driver_to_trip(trip_id):
    current_user_id = get_jwt_identity()

    # Récupérer les données du corps de la requête
    data = request.get_json()

    # Debugging: Afficher le corps de la requête pour vérifier sa structure
    print("Données reçues :", data)

    # Vérifier que driver_id est bien présent dans les données
    driver_id = data.get('driver_id')

    if not driver_id:
        return jsonify({"message": "Driver ID is required"}), 400

    # Vérification de l'existence du conducteur
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({"message": "Driver not found"}), 404

    # Récupérer le trajet
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({"message": "Trip not found"}), 404

    # Assigner le conducteur au trajet
    trip.driver_id = driver_id
    trip.status = "assigned"  # Marquer le trajet comme "assigné"

    try:
        db.session.commit()
        return jsonify({"message": "Driver assigned successfully", "trip_id": trip.id, "driver_id": driver_id}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error assigning driver: {str(e)}"}), 500


#Route pour mettre à jour l'état du trajet
@app.route('/trips/<int:trip_id>', methods=['PUT'])
@jwt_required()
def update_trip_status(trip_id):
    """
    Met à jour le statut d'un trajet en fonction de son ID.
    Le statut peut être 'pending', 'in_progress', 'completed', etc.
    """
    current_user_id = get_jwt_identity()  # Récupère l'ID de l'utilisateur connecté

    # Récupérer les données envoyées dans la requête
    data = request.get_json()

    new_status = data.get('status')  # Statut à mettre à jour (ex: 'in_progress', 'completed', etc.)

    # Vérification du statut
    if new_status not in ['pending', 'in_progress', 'completed', 'cancelled']:
        return jsonify({"message": "Invalid status value"}), 400

    # Récupérer le trajet correspondant à l'ID
    trip = Trip.query.get(trip_id)
    if not trip:
        return jsonify({"message": "Trip not found"}), 404

    # Vérifier si l'utilisateur actuel est le propriétaire ou le conducteur de la commande
    if trip.user_id != current_user_id and (trip.driver_id is not None and trip.driver_id != current_user_id):
        return jsonify({"message": "You do not have permission to update this trip"}), 403

    # Mettre à jour le statut de la commande
    trip.status = new_status

    # Sauvegarder les modifications dans la base de données
    try:
        db.session.commit()
        return jsonify({
            "message": "Trip status updated successfully",
            "trip_id": trip.id,
            "new_status": trip.status
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error updating trip status: {str(e)}"}), 500


# Lancer l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
