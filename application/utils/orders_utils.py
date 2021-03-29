def get_ids(items: list[dict]) -> list[int]:
    """
    Get list with ids of orders
    """
    return [item['id'] for item in items]


def update_orders(orders: list[dict], new_orders: list[dict]) -> list[dict]:
    """
    Add to orders new_orders that don't exist already in orders
    """
    ids = get_ids(orders)
    for new in new_orders:
        if new['id'] not in ids:
            orders.append(new)
    return orders


def get_orders_weight(orders: list[dict]) -> float:
    if len(orders) != 0:
        orders_weight = sum([order['weight'] for order in orders])
    else:
        orders_weight = 0
    return orders_weight