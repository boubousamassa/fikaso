from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Order
from extensions import db

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration de la base de données
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fikaso.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'secret_key'  # Change ceci pour la production

# Initialisation de la base de données et de JWT
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Modèles de la base de données

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)

class Restaurant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    owner = db.relationship('User', backref=db.backref('restaurants', lazy=True))
    meals = db.relationship('Meal', backref='restaurant', lazy=True)

class Meal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meal.id'), nullable=False)
    status = db.Column(db.String(100), default='Pending')  # Pending, Delivered, etc.
    user = db.relationship('User', backref=db.backref('orders', lazy=True))
    meal = db.relationship('Meal', backref=db.backref('orders', lazy=True))

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
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid credentials'}), 401


# Passer une commande
@app.route('/orders', methods=['POST'])
@jwt_required()
def place_order():
    data = request.get_json()
    meal_id = data['meal_id']
    user_id = get_jwt_identity()

    new_order = Order(user_id=user_id, meal_id=meal_id)
    db.session.add(new_order)
    db.session.commit()

    return jsonify({'message': 'Order placed successfully'}), 201

# Liste des commandes d'un utilisateur
@app.route('/orders', methods=['GET'])
@jwt_required()
def get_orders():
    user_id = get_jwt_identity()
    orders = Order.query.filter_by(user_id=user_id).all()
    return jsonify([{'id': o.id, 'meal': o.meal.name, 'status': o.status} for o in orders])

#Cette route permet à un utilisateur authentifié d'ajouter un restaurant.
@app.route('/restaurants', methods=['POST'])
@jwt_required()
def add_restaurant():
    current_user_id = get_jwt_identity()  # ID de l'utilisateur authentifié
    data = request.get_json()

    name = data.get('name')
    address = data.get('address')

    if not name or not address:
        return jsonify({'message': 'Missing name or address'}), 400

    # Créer un restaurant
    new_restaurant = Restaurant(name=name, address=address, owner_id=current_user_id)

    try:
        db.session.add(new_restaurant)
        db.session.commit()
        return jsonify({'message': 'Restaurant added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500

#Cette route permet de lister tous les restaurants de l'utilisateur authentifié.
@app.route('/restaurants', methods=['GET'])
@jwt_required()
def get_restaurants():
    current_user_id = get_jwt_identity()

    # Récupérer tous les restaurants de l'utilisateur
    restaurants = Restaurant.query.filter_by(owner_id=current_user_id).all()

    if not restaurants:
        return jsonify({'message': 'No restaurants found'}), 404

    # Formater la réponse
    restaurants_list = []
    for restaurant in restaurants:
        restaurants_list.append({
            'id': restaurant.id,
            'name': restaurant.name,
            'address': restaurant.address
        })

    return jsonify(restaurants_list), 200

#Cette route permet d'ajouter un repas à un restaurant.
@app.route('/restaurants/<int:restaurant_id>/meals', methods=['POST'])
@jwt_required()
def add_meal(restaurant_id):
    current_user_id = get_jwt_identity()

    # Vérifier si le restaurant appartient à l'utilisateur
    restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=current_user_id).first()
    if not restaurant:
        return jsonify({'message': 'Restaurant not found or not owned by you'}), 404

    data = request.get_json()

    name = data.get('name')
    description = data.get('description')
    price = data.get('price')

    if not name or price is None:
        return jsonify({'message': 'Missing name or price'}), 400

    # Créer un repas
    new_meal = Meal(name=name, description=description, price=price, restaurant_id=restaurant_id)

    try:
        db.session.add(new_meal)
        db.session.commit()
        return jsonify({'message': 'Meal added successfully'}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Error: {str(e)}'}), 500

#Cette route permet de lister tous les repas d'un restaurant.
@app.route('/restaurants/<int:restaurant_id>/meals', methods=['GET'])
@jwt_required()
def get_meals(restaurant_id):
    current_user_id = get_jwt_identity()

    # Vérifier si le restaurant appartient à l'utilisateur
    restaurant = Restaurant.query.filter_by(id=restaurant_id, owner_id=current_user_id).first()
    if not restaurant:
        return jsonify({'message': 'Restaurant not found or not owned by you'}), 404

    # Récupérer tous les repas du restaurant
    meals = Meal.query.filter_by(restaurant_id=restaurant_id).all()

    if not meals:
        return jsonify({'message': 'No meals found for this restaurant'}), 404

    # Formater la réponse
    meals_list = []
    for meal in meals:
        meals_list.append({
            'id': meal.id,
            'name': meal.name,
            'description': meal.description,
            'price': meal.price
        })

    return jsonify(meals_list), 200

@app.route('/orders', methods=['POST'])
@jwt_required()
def create_order():
    current_user_id = get_jwt_identity()
    data = request.get_json()

    # Validation des données
    restaurant_id = data.get('restaurant_id')
    delivery_address = data.get('delivery_address')
    items = data.get('items')  # JSON list of items
    total_price = data.get('total_price')

    if not all([restaurant_id, delivery_address, items, total_price]):
        return jsonify({"message": "All fields are required"}), 400

    # Vérification que le restaurant existe
    restaurant = Restaurant.query.get(restaurant_id)
    if not restaurant:
        return jsonify({"message": "Restaurant not found"}), 404

    # Création de la commande
    new_order = Order(
        user_id=current_user_id,
        restaurant_id=restaurant_id,
        delivery_address=delivery_address,
        items=items,
        total_price=total_price,
    )

    try:
        db.session.add(new_order)
        db.session.commit()
        return jsonify({"message": "Order created successfully", "order_id": new_order.id}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error: {str(e)}"}), 500

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


# Lancer l'application Flask
if __name__ == '__main__':
    app.run(debug=True)
