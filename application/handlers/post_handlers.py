from application.collections_db import Couriers, Orders


def post_couriers(couriers_data, couriers_db: Couriers):
    posted_ids = couriers_db.add_items(couriers_data['data'])
    return {'couriers': [{'id': i} for i in posted_ids]}


def post_orders(orders_data, orders_db: Orders):
    posted_ids = orders_db.add_items(orders_data['data'])
    return {'orders': [{'id': i} for i in posted_ids]}