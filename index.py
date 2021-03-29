from flask import Flask, request, Response
import json
from handlers import post_couriers, post_orders, patch_courier, assign_orders, complete_order, get_courier
from collections_db import Couriers, Orders
from pymongo import MongoClient
import validator
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client['slasti']

couriers_db = Couriers(db['couriers'])
orders_db = Orders(db['orders'])


# TODO: валидировать complete_time
# TODO: структура и названия
# TODO: типы переменных
# TODO: документация
# TODO: разобраться с assign time
# TODO: сделать readmi
# TODO: сделать requirements
@app.route('/couriers', methods=['POST'])
def add_couriers():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    couriers_data = request.get_json()
    data, status = validator.validate_couriers(couriers_data)
    if status == 201:
        data = post_couriers(data, couriers_db)
    return Response(json.dumps(data), status, headers={'Content-Type': 'application/json'})


@app.route('/couriers/<courier_id>', methods=['PATCH'])
def update_courier(courier_id):
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    new_data = request.get_json()
    data, status = validator.validate_update_courier(new_data, courier_id, couriers_db)
    if status == 200:
        data = patch_courier(courier_id, new_data, couriers_db, orders_db)
    return Response(json.dumps(data), status, headers={'Content-Type': 'application/json'})


@app.route('/orders', methods=['POST'])
def add_orders():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    orders_data = request.get_json()
    data, status = validator.validate_orders(orders_data)
    if status == 201:
        data = post_orders(data, orders_db)
    return Response(json.dumps(data), status, headers={'Content-Type': 'application/json'})


@app.route('/orders/assign', methods=['POST'])
def post_orders_assign():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    courier_id_data = request.get_json()
    data, status = validator.validate_assign_orders(courier_id_data, couriers_db)
    if status == 200:
        data = assign_orders(courier_id_data, couriers_db, orders_db)  # TODO: rename to post_assign_orders
    return Response(json.dumps(data), status, headers={'Content-Type': 'application/json'})


@app.route('/orders/complete', methods=['POST'])
def post_order_complete():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    complete_data = request.get_json()
    data, status = validator.validate_complete_orders(complete_data, couriers_db, orders_db)
    if status == 200:
        data = complete_order(data, couriers_db, orders_db)  # TODO: rename to post_complete_order
    return Response(json.dumps(data), status, headers={'Content-Type': 'application/json'})


@app.route('/couriers/<courier_id>', methods=['GET'])
def get_courier_info(courier_id):
    data, status = validator.validate_courier_id(courier_id, couriers_db)
    if status == 200:
        data = get_courier(courier_id, couriers_db, orders_db)
    return Response(json.dumps(data), status=200, headers={'Content-Type': 'application/json'})


if __name__ == "__main__":
    app.run()
    # app.run(host='0.0.0.0', port='8080')
