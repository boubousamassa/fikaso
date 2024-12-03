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

class Driver(db.Model):
    __tablename__ = 'drivers'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    # Autres champs pour les conducteurs


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
    status = db.Column(db.String(50), default="pending", nullable=False)  # Nouveau champ

    def get_items(self):
        return json.loads(self.items)  # Convertir la chaîne JSON en liste Python


# Modèle pour les trajets (livraison à la demande)
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


