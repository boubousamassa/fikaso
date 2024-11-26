from fikaso.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from fikaso.extensions import db


class UserService:
    @staticmethod
    def create_user(username, password):
        """ Crée un nouvel utilisateur """
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return None, "Utilisateur déjà existant"

        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return new_user, "Utilisateur créé avec succès"

    @staticmethod
    def authenticate_user(username, password):
        """ Authentifie un utilisateur """
        user = User.query.filter_by(username=username).first()
        if not user or not check_password_hash(user.password, password):
            return None, "Nom d'utilisateur ou mot de passe incorrect"
        return user, "Authentification réussie"

    @staticmethod
    def get_user_profile(user_id):
        """ Récupère les informations d'un utilisateur par son ID """
        user = User.query.get(user_id)
        if not user:
            return None, "Utilisateur non trouvé"
        return user, "Profil récupéré avec succès"
