from copy import deepcopy
from application.utils.datetime_utils import parse_intervals
from application.collections_db import Couriers, Orders
from application.utils.orders_utils import get_ids, get_orders_weight
from application.handlers.assign_handler import COURIERS_CAPACITY
from typing import List


def patch_courier(courier_id, new_data: dict, couriers_db: Couriers, orders_db: Orders):
    """
    Change data for courier with courier_id and remove orders from assigned orders,
    if they don't fit by region, delivery hours or weight anymore
    """
    courier_id = int(courier_id)
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
    orders_db.update_status(dropped_orders, 0, courier_type='')

    # Get edited courier's data from DB
    edited_courier = couriers_db.get_item(courier_id)
    return {'courier_id': edited_courier['_id'],
            'courier_type': edited_courier['courier_type'],
            'regions': edited_courier['regions'],
            'working_hours': edited_courier['working_hours']}


def _is_intervals_fitted(working_hours: List[str], delivery_intervals: List[dict]) -> bool:
    """
    Check if the order fit the courier by delivery hours
    """
    working_intervals = parse_intervals(working_hours)

    is_fitted = []
    for work_start, work_end in working_intervals:
        for order_interval in delivery_intervals:
            is_fitted.append(work_start < order_interval['end'] and work_end > order_interval['start'])

    return any(is_fitted)


def _get_courier_capacity(courier_type: str, assigned_orders: List[dict]) -> float:
    """
    Calculate how much courier can lift, if he already get assigned_orders
    """
    all_capacity = COURIERS_CAPACITY[courier_type]
    orders_weight = get_orders_weight(assigned_orders)
    return all_capacity - orders_weight


def _replace_orders(placed_orders: List[dict], capacity) -> List[dict]:
    """
    Greedy algorithm to release courier's bag
    """
    desc_orders = sorted(placed_orders, key=lambda order: order['weight'], reverse=True)
    while capacity < 0 and len(desc_orders) != 0:
        order = desc_orders.pop(0)
        capacity += order['weight']
    return desc_orders