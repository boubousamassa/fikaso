from datetime import datetime
from extensions import db
import json


# Modèle pour l'utilisateur
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    # Relation avec les restaurants
    restaurants = db.relationship('Restaurant', backref='owner', lazy=True)


# Modèle pour les restaurants
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

# Modèle pour les commandes
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


# Modèle pour les conducteurs (ajouté)
class Driver(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone_number = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Driver {self.name}>"


# Modèle pour les trajets (livraison à la demande)
class Trip(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver.id'), nullable=True)
    origin = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), default='requested')  # requested, in_progress, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relations avec User et Driver
    user = db.relationship('User', backref=db.backref('trips'))
    driver = db.relationship('Driver', backref=db.backref('trips'))

    def __repr__(self):
        return f"<Trip {self.id} - {self.status}>"
