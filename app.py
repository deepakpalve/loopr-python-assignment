from flask import Flask, request
from flask_restful import Resource, Api
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from tinydb import TinyDB, Query
import base64

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'your-secret-key'
api = Api(app)
jwt = JWTManager(app)
db = TinyDB('db.json')

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def json(self):
        return {
            'username': self.username,
            'password': self.password
        }

class UserRegistration(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        new_user = User(username, password)
        db.insert(new_user.json())
        return {'message': 'User created successfully'}, 201

class UserLogin(Resource):
    def post(self):
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        User = Query()
        user = db.search(User.username == username and User.password == password)
        if not user:
            return {'message': 'Invalid credentials'}, 401

        access_token = create_access_token(identity=username)
        return {'access_token': access_token}, 200

class ShoppingCart(Resource):
    @jwt_required()
    def get(self, user_id):
        CartItem = Query()
        items = db.search(CartItem.user_id == user_id)
        return {'items': items}, 200

    @jwt_required()
    def post(self, user_id):
        data = request.get_json()
        product_id = data.get('product_id')
        image = data.get('image')
        name = data.get('name')
        price = data.get('price')
        quantity = data.get('quantity')

        # Convert image to base64-encoded string
        image_data = base64.b64encode(image)

        CartItem = Query()
        item = {
            'user_id': user_id,
            'product_id': product_id,
            'image': image_data.decode('utf-8'),
            'name': name,
            'price': price,
            'quantity': quantity
        }
        db.insert(item)
        return {'message': 'Item added to cart'}, 201

    @jwt_required()
    def put(self, user_id, item_id):
        data = request.get_json()
        quantity = data.get('quantity')

        CartItem = Query()
        db.update({'quantity': quantity}, (CartItem.user_id == user_id) & (CartItem.doc_id == item_id))
        return {'message': 'Item updated'}, 200

    @jwt_required()
    def delete(self, user_id, item_id):
        CartItem = Query()
        db.remove((CartItem.user_id == user_id) & (CartItem.doc_id == item_id))
        return {'message': 'Item deleted'}, 200

api.add_resource(UserRegistration, '/register')
api.add_resource(UserLogin, '/login')
api.add_resource(ShoppingCart, '/cart/<string:user_id>', '/cart/<string:user_id>/<int:item_id>')

if __name__ == '__main__':
    app.run(debug=True)
