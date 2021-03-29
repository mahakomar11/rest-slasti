from application.utils.datetime_utils import str_to_datetime
from application.collections_db import Couriers, Orders
from application.utils.orders_utils import get_ids
from datetime import datetime


def complete_order(complete_data, couriers_db: Couriers, orders_db: Orders):
    courier_id = complete_data['courier_id']
    order_id = complete_data['order_id']
    complete_time = str_to_datetime(complete_data['complete_time'])

    courier_type = couriers_db.get_item(courier_id)['courier_type']
    delivery_time = _calculate_delivery_time(courier_id, complete_time, couriers_db, orders_db)
    # Update data of completed order in DB
    orders_db.update_status([{'id': order_id}], 2,
                            complete_time=complete_time,
                            delivery_time=delivery_time,
                            courier_type=courier_type)
    # Change status of order in couriers' DB
    couriers_db.move_order_to_completed(courier_id, order_id)
    return {'order_id': order_id}


def _calculate_delivery_time(courier_id, complete_time: datetime, couriers_db, orders_db):
    courier = couriers_db.get_item(courier_id)

    completed_orders_ids = get_ids(courier['completed_orders'])
    assign_time: datetime = courier['assign_time']

    if len(completed_orders_ids) == 0:
        return (complete_time - assign_time).total_seconds()

    completed_orders = orders_db.get_items_by_ids(completed_orders_ids)
    previous_time = _find_previous_time(assign_time, completed_orders)

    return (complete_time - previous_time).total_seconds()


def _find_previous_time(assign_time: datetime, completed_orders):
    previous_order_time = max([order['complete_time'] for order in completed_orders])
    return max(assign_time, previous_order_time)  # Return the nearest time
