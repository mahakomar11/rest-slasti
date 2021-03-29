from application.handlers.orders_utils import get_ids
from application.collections_db import Couriers, Orders
from statistics import mean

COURIER_COST = {'foot': 2, 'bike': 5, 'car': 9}


def get_courier(courier_id, couriers_db: Couriers, orders_db: Orders):
    courier_id = int(courier_id)
    courier = couriers_db.get_item(courier_id)

    completed_orders_ids = get_ids(courier['completed_orders'])
    # If no completed orders, no rating and earning returns
    if len(completed_orders_ids) == 0:
        return {'courier_id': courier_id,
                'courier_type': courier['courier_type'],
                'regions': courier['regions'],
                'working_hours': courier['working_hours']}

    completed_orders = orders_db.get_items_by_ids(completed_orders_ids)
    rating, earning = _calculate_rating_and_earning(completed_orders)
    return {'courier_id': courier_id,
            'courier_type': courier['courier_type'],
            'regions': courier['regions'],
            'working_hours': courier['working_hours'],
            'rating': rating,
            'earning': earning}


def _calculate_rating_and_earning(completed_orders):
    # Calculate min of mean times through regions and earning
    t_regions = {}
    earning = 0
    for order in completed_orders:
        if order['region'] in t_regions:
            t_regions[order['region']].append(order['delivery_time'])
        else:
            t_regions[order['region']] = [order['delivery_time']]
        earning += 500 * COURIER_COST[order['courier_type']]
    t_mean_regions = {reg: mean(times) for reg, times in t_regions.items()}
    t_min = min(t_mean_regions)

    # Calculate rating
    rating = round((60 * 60 - min(t_min, 60 * 60)) / (60 * 60) * 5, 2)

    return rating, earning