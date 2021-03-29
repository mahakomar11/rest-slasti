from application.collections_db import Couriers, Orders


def post_couriers(couriers_data: dict, couriers_db: Couriers):
    """
    Add couriers to DB
    """
    posted_ids = couriers_db.add_items(couriers_data['data'])
    return {'couriers': [{'id': i} for i in posted_ids]}


def post_orders(orders_data: dict, orders_db: Orders):
    """
    Add orders to DB
    """
    posted_ids = orders_db.add_items(orders_data['data'])
    return {'orders': [{'id': i} for i in posted_ids]}
