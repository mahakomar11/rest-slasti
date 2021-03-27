from pymongo import MongoClient
from copy import deepcopy
from interval_parser import parse_interval
from datetime import datetime
from collections_db import Couriers, Orders

COURIERS_CAPACITY = {'foot': 10, 'bike': 15, 'car': 50}


def post_couriers(couriers, couriers_db: Couriers):
    posted_couriers = couriers_db.add_items(couriers)
    # handle answer
    return posted_couriers


def post_orders(orders, orders_db: Orders):
    posted_orders = orders_db.add_items(orders)
    return posted_orders


def patch_courier(courier_id, new_data, couriers_db: Couriers):
    couriers_db.edit_item(courier_id, new_data)
    return couriers_db.get_item(courier_id)


def assign_orders(courier_id, couriers_db: Couriers, orders_db: Orders):
    courier = couriers_db.get_item(courier_id)

    assigned_orders = courier['assigned_orders']  # orders that already in courier's bag

    # Set assign time
    if len(assigned_orders) == 0:
        assign_time = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
    else:
        assign_time = courier['assign_time']

    # Find orders that fit time intervals
    intervals = [parse_interval(wh) for wh in courier['working_hours']]  # get intervals in seconds
    orders_to_place = []
    for interval in intervals:
        fitted_orders = orders_db.get_fitted_orders(interval[0], interval[1], courier['regions'])
        _update_orders(orders_to_place, fitted_orders)

    # Put all possible new orders to courier's bag
    capacity = _get_courier_capacity(courier, assigned_orders, orders_db)
    new_assigned_orders = _place_orders(orders_to_place, capacity)
    _update_orders(assigned_orders, new_assigned_orders)

    if len(assigned_orders) != 0:
        couriers_db.write_assigned_orders(courier_id, assigned_orders, assign_time)

    if len(new_assigned_orders) != 0:
        orders_db.update_status(new_assigned_orders, 1)

    return assigned_orders


def _get_courier_capacity(courier, courier_orders, orders_db):
    all_capacity = COURIERS_CAPACITY[courier['courier_type']]

    if len(courier_orders) != 0:
        orders_ids = [order['id'] for order in courier_orders]
        orders = orders_db.get_items_by_ids(orders_ids)
        orders_weight = sum([order['weight'] for order in orders])
    else:
        orders_weight = 0

    return all_capacity - orders_weight


def complete_order(courier_id, order_id, complete_time, couriers_db: Couriers, orders_db: Orders):
    print(courier_id, order_id)
    orders_db.update_status([{'id': order_id}], 2, complete_time=complete_time)
    couriers_db.move_order_to_completed(courier_id, order_id)
    return order_id


def _update_orders(orders, new_orders):
    ids = [order['id'] for order in orders]
    for new in new_orders:
        if new['id'] not in ids:
            orders.append(new)


def _place_orders(orders, capacity):
    # Greedy algorithm
    desc_orders = sorted(orders, key=lambda order: order['weight'], reverse=True)
    placed_orders = []
    while capacity >= 0 and len(desc_orders) != 0:
        order = desc_orders.pop(0)
        if order['weight'] <= capacity:
            placed_orders.append({'id': order['id']})
            capacity -= order['weight']
    return placed_orders


if __name__ == '__main__':
    import json

    client = MongoClient('localhost', 27017)
    db = client['slasti']

    couriers_db = Couriers(db['couriers'])
    orders_db = Orders(db['orders'])

    i = couriers_db.get_item(7)
    # with open('cs_data.json') as f:
    #     couriers_data = json.load(f)
    # post_couriers(couriers_data['data'], couriers_db)
    #
    # with open('od_data.json') as f:
    #     orders_data = json.load(f)
    # post_orders(orders_data['data'], orders_db)
    #
    #
    # assigned_orders = assign_orders(1, couriers_db, orders_db)
    # print(assigned_orders)
    print('h')