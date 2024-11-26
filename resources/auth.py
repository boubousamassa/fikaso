from flask_restful import Resource
from flask import request
from flask_jwt_extended import create_access_token
from fikaso.resources.user import UserService  # Import du service utilisateur

class UserRegister(Resource):
    def post(self):
        data = request.get_json()
        user, message = UserService.create_user(data['username'], data['password'])
        if not user:
            return {"message": message}, 400
        return {"message": message}, 201

class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        user, message = UserService.authenticate_user(data['username'], data['password'])
        if not user:
            return {"message": message}, 401
        access_token = create_access_token(identity=user.id)
        return {"access_token": access_token}, 200
