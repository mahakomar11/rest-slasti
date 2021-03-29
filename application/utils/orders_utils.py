from typing import List


def get_ids(items: List[dict]) -> List[int]:
    """
    Get list with ids of orders
    """
    return [item['id'] for item in items]


def update_orders(orders: List[dict], new_orders: List[dict]) -> List[dict]:
    """
    Add to orders new_orders that don't exist already in orders
    """
    ids = get_ids(orders)
    for new in new_orders:
        if new['id'] not in ids:
            orders.append(new)
    return orders


def get_orders_weight(orders: List[dict]) -> float:
    if len(orders) != 0:
        orders_weight = sum([order['weight'] for order in orders])
    else:
        orders_weight = 0
    return orders_weight
