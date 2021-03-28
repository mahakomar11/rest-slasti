from pymongo import MongoClient
from copy import deepcopy
from datetime_utils import parse_interval
from datetime import datetime
from collections_db import Couriers, Orders
from strict_rfc3339 import now_to_rfc3339_utcoffset as get_now

COURIERS_CAPACITY = {'foot': 10, 'bike': 15, 'car': 50}


def post_couriers(couriers_data, couriers_db: Couriers):
    posted_ids = couriers_db.add_items(couriers_data['data'])
    return {'couriers': [{'id': i} for i in posted_ids]}


def post_orders(orders_data, orders_db: Orders):
    posted_ids = orders_db.add_items(orders_data['data'])
    return {'orders': [{'id': i} for i in posted_ids]}


def patch_courier(courier_id, new_data, couriers_db: Couriers, orders_db: Orders):
    courier_id = int(courier_id)
    # Check if changed something that affects to assigned orders
    courier = couriers_db.get_item(courier_id)

    # Get assigned orders' data and create copy of its list
    assigned_orders_ids = get_ids(courier['assigned_orders'])
    assigned_orders = orders_db.get_items_by_ids(assigned_orders_ids)
    new_assigned_orders = deepcopy(assigned_orders)

    # Remove orders, that don't fit anymore, from assigned_orders
    if 'regions' in new_data:
        new_assigned_orders = list(filter(lambda o: o['region'] in new_data['regions'],
                                          new_assigned_orders))
    if 'working_hours' in new_data:
        new_assigned_orders = list(filter(lambda o: _is_intervals_fitted(new_data['working_hours'], o['intervals']),
                                          new_assigned_orders))
    if 'courier_type' in new_data and \
            COURIERS_CAPACITY[new_data['courier_type']] < COURIERS_CAPACITY[courier['courier_type']]:
        # if capacity of courier get down
        new_capacity = _get_courier_capacity(new_data['courier_type'], new_assigned_orders)
        new_assigned_orders = _replace_orders(new_assigned_orders, new_capacity)

    # Add edited assigned list to new data and edit courier data in DB
    new_data['assigned_orders'] = [{'id': order['id']} for order in new_assigned_orders]
    couriers_db.edit_item(courier_id, new_data)

    # Update status to 0 (not assigned) for orders that are not in new assigned orders
    dropped_orders = [{'id': order['id']} for order in assigned_orders if order not in new_assigned_orders]
    orders_db.update_status(dropped_orders, 0)

    # Get edited courier's data from DB
    edited_courier = couriers_db.get_item(courier_id)
    return {'courier_id': edited_courier['_id'],
            'courier_type': edited_courier['courier_type'],
            'regions': edited_courier['regions'],
            'working_hours': edited_courier['working_hours']}


def assign_orders(courier_id_data, couriers_db: Couriers, orders_db: Orders):
    courier_id = courier_id_data['courier_id']
    courier = couriers_db.get_item(courier_id)

    assigned_orders_ids = get_ids(courier['assigned_orders'])  # ids of orders that already in courier's bag

    # Set assign time
    if len(assigned_orders_ids) == 0:
        assigned_orders = []
        assign_time = get_now(integer=False)
    else:
        assigned_orders = orders_db.get_items_by_ids(assigned_orders_ids)
        assign_time = courier['assign_time']

    # Find orders that fit time intervals
    intervals = [parse_interval(wh) for wh in courier['working_hours']]  # get intervals in seconds
    orders_to_place = []
    for interval in intervals:
        fitted_orders = orders_db.get_fitted_orders(interval[0], interval[1], courier['regions'])
        orders_to_place = _update_orders(orders_to_place, fitted_orders)

    # Put all possible new orders to courier's bag
    capacity = _get_courier_capacity(courier['courier_type'], assigned_orders)
    new_assigned_orders = _place_orders(orders_to_place, capacity)
    assigned_orders = _update_orders(assigned_orders, new_assigned_orders)

    # Write assigned orders to DB (if it is empty list, it is already in DB)
    if len(assigned_orders) != 0:
        couriers_db.write_assigned_orders(courier_id, assigned_orders, assign_time)
    # Update status to 1 for assigned orders in DB
    if len(new_assigned_orders) != 0:
        orders_db.update_status(new_assigned_orders, 1)

    # Get assigned orders from DB
    courier = couriers_db.get_item(courier_id)
    return {'orders': [{'id': o['id']} for o in courier['assigned_orders']],
            'assign_time': courier['assign_time']}


def complete_order(complete_data, couriers_db: Couriers, orders_db: Orders):
    courier_id = complete_data['courier_id']
    order_id = complete_data['order_id']
    complete_time = complete_data['complete_time']

    print(courier_id, order_id)
    orders_db.update_status([{'id': order_id}], 2, complete_time=complete_time)
    couriers_db.move_order_to_completed(courier_id, order_id)
    return {'order_id': order_id}


def get_ids(items):
    return [item['id'] for item in items]


def _is_intervals_fitted(working_hours, delivery_intervals):
    working_intervals = [parse_interval(wh) for wh in working_hours]

    is_fitted = []
    for work_start, work_end in working_intervals:
        for order_interval in delivery_intervals:
            is_fitted.append(work_start < order_interval['end'] and work_end > order_interval['start'])

    return any(is_fitted)


def _get_courier_capacity(courier_type, assigned_orders):
    all_capacity = COURIERS_CAPACITY[courier_type]
    orders_weight = _get_orders_weight(assigned_orders)
    return all_capacity - orders_weight


def _get_orders_weight(orders):
    if len(orders) != 0:
        orders_weight = sum([order['weight'] for order in orders])
    else:
        orders_weight = 0
    return orders_weight


def _update_orders(orders, new_orders):
    ids = [order['id'] for order in orders]
    for new in new_orders:
        if new['id'] not in ids:
            orders.append(new)
    return orders


def _place_orders(orders, capacity):
    # Greedy algorithm to fill courier's bag
    desc_orders = sorted(orders, key=lambda order: order['weight'], reverse=True)
    placed_orders = []
    while capacity >= 0 and len(desc_orders) != 0:
        order = desc_orders.pop(0)
        if order['weight'] <= capacity:
            placed_orders.append(order)
            capacity -= order['weight']
    return placed_orders


def _replace_orders(placed_orders, capacity):
    desc_orders = sorted(placed_orders, key=lambda order: order['weight'], reverse=True)
    while capacity < 0 and len(desc_orders) != 0:
        order = desc_orders.pop(0)
        capacity += order['weight']
    return desc_orders


if __name__ == '__main__':
    import json

    client = MongoClient('localhost', 27017)
    db = client['slasti']

    couriers_db = Couriers(db['couriers'])
    orders_db = Orders(db['orders'])

    # i = couriers_db.get_item(7)
    # with open('cs_data.json') as f:
    #     couriers_data = json.load(f)
    # response_data = post_couriers(couriers_data, couriers_db)
    #
    # with open('od_data.json') as f:
    #     orders_data = json.load(f)
    # response_data = post_orders(orders_data, orders_db)

    #
    # patch_response = patch_courier(1, {'courier_type': 'car'}, couriers_db, orders_db)
    # assigned_orders = assign_orders(1, couriers_db, orders_db)
    # patch_courier(1, {'courier_type': 'foot'}, couriers_db, orders_db)
    # patch_courier(1, {'working_hours': ['00:01-06:00']}, couriers_db, orders_db)
    # patch_courier(1, {'regions': [80]}, couriers_db, orders_db)
    # print(assigned_orders)
    complete_data = {
        'courier_id': 1,
        'order_id': 1,
        'complete_time': "2021-01-10T10:33:01.42Z"
    }
    complete_response = complete_order(complete_data, couriers_db, orders_db)
    print('h')
