from datetime import datetime
from extensions import db


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


    # Colonnes pour les plats
    dish_name = db.Column(db.String, nullable=False)
    dish_price = db.Column(db.Float, nullable=False)



# Modèle pour les articles de menu (MenuItem)
class MenuItem(db.Model):
    __tablename__ = 'menu_item'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    price = db.Column(db.Float, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)

    # Relation avec le restaurant
    restaurant = db.relationship('Restaurant', back_populates='menu_items')

    def __repr__(self):
        return f"<MenuItem {self.name} - {self.price}>"


# Modèle pour les commandes
class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # L'utilisateur qui passe la commande
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    delivery_address = db.Column(db.String(255), nullable=False)
    items = db.Column(db.Text, nullable=False)  # JSON des articles commandés
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(50), default="Pending")  # Pending, In Progress, Delivered, Cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Order {self.id} - Status: {self.status}>"


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
