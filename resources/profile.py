from flask_restful import Resource
from flask_jwt_extended import jwt_required, get_jwt_identity
from fikaso.models import User

class UserProfile(Resource):
    @jwt_required()
    def get(self):
        # Obtenir l'ID de l'utilisateur à partir du token JWT
        user_id = get_jwt_identity()

        # Récupérer l'utilisateur
        user = User.query.get(user_id)
        if not user:
            return {"message": "Utilisateur non trouvé"}, 404

        # Retourner les informations de l'utilisateur
        return {"username": user.username}, 200
