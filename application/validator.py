import json
from application.utils.datetime_utils import str_to_datetime, ValidatorWithDatetime
from application.collections_db import Couriers


def validate_couriers(couriers_data):
    with open('application/schemas/CouriersPostRequest.json') as f:
        couriers_post_schema = ValidatorWithDatetime(json.load(f))
    return _validate_post_items(couriers_data, couriers_post_schema, 'courier')


def validate_orders(orders_data):
    with open('application/schemas/OrdersPostRequest.json') as f:
        orders_post_schema = ValidatorWithDatetime(json.load(f))
    return _validate_post_items(orders_data, orders_post_schema, 'order')


def validate_update_courier(new_data, courier_id, couriers_db: Couriers):
    data, status = validate_courier_id(courier_id, couriers_db)
    if status == 400:
        return data, status

    with open('application/schemas/CouriersUpdateRequest.json') as f:
        courier_update_schema = ValidatorWithDatetime(json.load(f))

    if courier_update_schema.is_valid(new_data):
        return new_data, 200

    error_messages = []
    for err in courier_update_schema.iter_errors(new_data):
        error_messages.append(err.message)

    return {'validation_error': {'messages': error_messages}}, 400


def validate_assign_orders(courier_id_data, couriers_db):
    with open('application/schemas/OrdersAssignPostRequest.json') as f:
        assign_orders_schema = ValidatorWithDatetime(json.load(f))

    for err in assign_orders_schema.iter_errors(courier_id_data):
        return {'validation_error': err.message}, 400

    courier_id = courier_id_data['courier_id']
    if couriers_db.get_item(courier_id):
        return courier_id_data, 200
    else:
        return {'validation_error': f'There are no courier with id {courier_id}'}, 400


def validate_complete_orders(complete_data, couriers_db, orders_db):
    # Check if data matchs with the schema
    with open('application/schemas/OrdersCompletePostRequest.json') as f:
        complete_order_schema = ValidatorWithDatetime(json.load(f))
    for err in complete_order_schema.iter_errors(complete_data):
        return {'validation_error': err.message}, 400

    # Check if courier_id and order_id exist
    courier_id = complete_data['courier_id']
    order_id = complete_data['order_id']
    if not couriers_db.get_item(courier_id):
        return {'validation_error': f'There are no courier with id {courier_id}'}, 400
    elif not orders_db.get_item(order_id):
        return {'validation_error': f'There are no order with id {order_id}'}, 400

    # Check status of the order
    order_status = orders_db.get_item(order_id)['status']
    if order_status == 0:
        return {'validation_error': f'order with id {order_id} is not assigned'}, 400
    elif order_status == 2:
        return {'validation_error': f'order with id {order_id} is already completed'}, 400

    # Check that complete time is later than assign time
    courier = couriers_db.get_item(courier_id)
    assign_time = courier['assign_time']
    complete_time = str_to_datetime(complete_data['complete_time'])
    if complete_time < assign_time:
        return {'validation_error':
                    f'\'complete_time\' must be later than \'assign_time\': {assign_time.isoformat()}'}, 400

    # Check if the order is assigned to this courier
    assigned_orders = courier['assigned_orders']
    print(assigned_orders)
    if {'id': order_id} not in assigned_orders:
        return {
                   'validation_error': f'order with id {order_id} is assigned to another courier'}, 400

    return complete_data, 200


def validate_courier_id(courier_id, couriers_db: Couriers):
    courier_id = int(courier_id)
    if not couriers_db.get_item(courier_id):
        return {'validation_error': f'There are no courier with id {courier_id}'}, 400
    else:
        return {}, 200


def _validate_post_items(items_data, schema, item_name):
    if schema.is_valid(items_data):
        return items_data, 201

    invalid_items_ids = set()
    for err in schema.iter_errors(items_data):
        # If error occurs in {} or in {'data': ...}
        if list(err.path) == [] or err.path[-1] == 'data':
            return {'validation_error': err.message}, 400

        invalid_item = items_data['data'][err.path[1]]  # item, where error occurs

        # If this item is not 'object'
        if not isinstance(invalid_item, dict):
            return {'validation_error': '\'data\' must contain only objects'}, 400

        # If courier_id/order_id is not ok
        if f'{item_name}_id' not in invalid_item:
            return {'validation_error': f'\'{item_name}_id\' is a required property'}, 400
        if not isinstance(invalid_item[f'{item_name}_id'], int):
            return {'validation_error': f'\'{item_name}_id\' must be an integer'}, 400

        invalid_items_ids.add(invalid_item[f'{item_name}_id'])

    validation_message = {f'{item_name}s': [{'id': i} for i in invalid_items_ids]}
    return {'validation_error': validation_message}, 400
