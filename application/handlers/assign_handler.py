from application.utils.datetime_utils import parse_intervals
from datetime import datetime
from application.collections_db import Couriers, Orders
from application.utils.orders_utils import get_ids, update_orders
from typing import List

COURIERS_CAPACITY = {'foot': 10, 'bike': 15, 'car': 50}


def assign_orders(courier_id_data: dict, couriers_db: Couriers, orders_db: Orders):
    """
    Find orders that fit by region, delivery hours and put max number of them to assigned_orders.
    """
    courier_id = courier_id_data['courier_id']
    courier = couriers_db.get_item(courier_id)

    assigned_orders_ids = get_ids(courier['assigned_orders'])  # ids of orders that already in courier's bag

    # if courier has assigned orders, return them
    if len(assigned_orders_ids) != 0:
        courier = couriers_db.get_item(courier_id)
        return {'orders': [{'id': o['id']} for o in courier['assigned_orders']],
                'assign_time': courier['assign_time'].isoformat()}

    # Find orders that fit time intervals
    intervals = parse_intervals(courier['working_hours'])  # get intervals in seconds
    orders_to_place = []
    for interval in intervals:
        fitted_orders = orders_db.get_fitted_orders(interval[0], interval[1], courier['regions'])
        orders_to_place = update_orders(orders_to_place, fitted_orders)

    # Put all possible new orders to courier's bag
    courier_type = courier['courier_type']
    capacity = COURIERS_CAPACITY[courier['courier_type']]
    assigned_orders = _place_orders(orders_to_place, capacity)

    # Write assigned orders to DB (if it is empty list, it is already in DB) and update their statuses
    if len(assigned_orders) != 0:
        couriers_db.write_assigned_orders(courier_id, assigned_orders, assign_time=datetime.now())
        orders_db.update_status(assigned_orders, 1, courier_type=courier_type)

    # Get assigned orders from DB
    courier = couriers_db.get_item(courier_id)
    return {'orders': [{'id': o['id']} for o in courier['assigned_orders']],
            'assign_time': courier['assign_time'].isoformat()}


def _place_orders(orders: List[dict], capacity) -> List[dict]:
    """
    Greedy algorithm to fill courier's bag
    """
    asc_orders = sorted(orders, key=lambda order: order['weight'])
    placed_orders = []
    while capacity >= 0 and len(asc_orders) != 0:
        order = asc_orders.pop(0)
        if order['weight'] <= capacity:
            placed_orders.append(order)
            capacity -= order['weight']
    return placed_orders
