from app import app
from extensions import db

with app.app_context():
    db.create_all()  # Crée toutes les tables dans la base de données
