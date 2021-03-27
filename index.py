from flask import Flask, request, Response
import json
from handlers import post_couriers, post_orders, patch_courier, assign_orders, complete_order
from collections_db import Couriers, Orders
from pymongo import MongoClient
import validator
from werkzeug.exceptions import BadRequest

app = Flask(__name__)

client = MongoClient('localhost', 27017)
db = client['slasti']

couriers_db = Couriers(db['couriers'])
orders_db = Orders(db['orders'])


# TODO: валидация интервалов и дат
# TODO: нормальные ответы
# TODO: reassign orders when patch courier
# TODO: подсчёт времени доставки
# TODO: get courier rating
# TODO: структура и названия
# TODO: типы переменных
# TODO: документация
@app.route('/couriers', methods=['POST'])
def add_couriers():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    couriers_data = request.get_json()
    data, status = validator.validate_couriers(couriers_data)
    if status == 201:
        data = post_couriers(data['data'], couriers_db)
    return Response(json.dumps(data), status)


@app.route('/couriers/<courier_id>', methods=['PATCH'])
def update_courier(courier_id):
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    new_data = request.get_json()
    data, status = validator.validate_update_courier(new_data)
    if status == 200:
        data = patch_courier(int(courier_id), new_data, couriers_db)
    return Response(json.dumps(data), status)


@app.route('/orders', methods=['POST'])
def add_orders():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    orders_data = request.get_json()
    data, status = validator.validate_orders(orders_data)
    if status == 201:
        data = post_orders(data['data'], orders_db)
    return Response(json.dumps(data), status)


@app.route('/orders/assign', methods=['POST'])
def post_orders_assign():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    courier_id_data = request.get_json()
    data, status = validator.validate_assign_orders(courier_id_data, couriers_db)
    if status == 200:
        data = assign_orders(courier_id_data['courier_id'], couriers_db, orders_db)  # TODO: rename to post_assign_orders
    return Response(json.dumps(data), status)


@app.route('/orders/complete', methods=['POST'])
def post_order_complete():
    if not request.is_json:
        raise BadRequest('Content-Type must be application/json')

    complete_data = request.get_json()
    data, status = validator.validate_complete_orders(complete_data, couriers_db, orders_db)
    print(status)
    if status == 200:
        data = complete_order(data['courier_id'], data['order_id'], data['complete_time'],
                              couriers_db,
                              orders_db)  # TODO: rename to post_complete_order
    return Response(json.dumps(data), status)


if __name__ == "__main__":
    app.run()
    # app.run(host='0.0.0.0', port='8080')
