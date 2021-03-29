def get_ids(items):
    return [item['id'] for item in items]


def update_orders(orders, new_orders):
    ids = get_ids(orders)
    for new in new_orders:
        if new['id'] not in ids:
            orders.append(new)
    return orders


def get_orders_weight(orders):
    if len(orders) != 0:
        orders_weight = sum([order['weight'] for order in orders])
    else:
        orders_weight = 0
    return orders_weight