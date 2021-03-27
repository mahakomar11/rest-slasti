from pymongo import MongoClient, collection as MongoCollection
from pymongo.errors import BulkWriteError
from copy import deepcopy
from datetime_utils import parse_interval


class CollectionDB:
    def __init__(self, collection: MongoCollection):
        self.collection = collection

    def add_items(self, items: list[dict]) -> list:
        try:
            self.collection.insert_many(items)
        except BulkWriteError:
            return []

        return items

    def edit_item(self, item_id: int, new_data: dict):
        self.collection.update_one({'_id': item_id}, {'$set': new_data})

    def get_item(self, item_id: int):
        return self.collection.find_one(item_id)


class Couriers(CollectionDB):
    def __init__(self, collection: MongoCollection):
        super().__init__(collection)

    def add_items(self, items: list[dict]):
        couriers = deepcopy(items)
        for courier in couriers:
            courier['_id'] = courier['courier_id']
            del courier['courier_id']

            courier['assigned_orders'] = []
            courier['completed_orders'] = []

        return super().add_items(couriers)

    def write_assigned_orders(self, courier_id: int, orders: list, assign_time):
        self.edit_item(courier_id, {'assigned_orders': [{'id': order['id']} for order in orders],
                                    'assign_time': assign_time})

    def move_order_to_completed(self, courier_id: int, order_id: int):
        self.collection.update_one({'_id': courier_id},
                                   {'$pull': {
                                       'assigned_orders': {'id': order_id}
                                   }})
        self.collection.update_one({'_id': courier_id},
                                   {'$push': {
                                       'completed_orders': {'id': order_id}
                                   }})


class Orders(CollectionDB):
    def __init__(self, collection: MongoCollection):
        super().__init__(collection)

    def get_items_by_ids(self, orders_ids: list[int]):
        return self.collection.find({'_id': {'$in': orders_ids}})

    def add_items(self, items: list[dict]):
        orders = deepcopy(items)
        for order in orders:
            order['_id'] = order['order_id']
            del order['order_id']

            intervals = [parse_interval(dh) for dh in order['delivery_hours']]
            order['intervals'] = [{'start': start, 'end': end} for start, end in intervals]

            order['status'] = 0

        return super().add_items(orders)

    def get_fitted_orders(self, time_start: int, time_end: int, regions: list) -> list[dict]:
        results = self.collection.find({'status': 0,
                                        'region': {'$in': regions},
                                        'intervals':
                                            {'$elemMatch':
                                                 {'start': {'$lte': time_start},
                                                  'end': {'$gte': time_end}
                                                  }
                                             }
                                        }, {'_id': 1, 'weight': 1})
        fitted_orders = [{'id': res['_id'], 'weight': res['weight']} for res in results]
        return fitted_orders

    def update_status(self, new_orders: list[dict], status: int, complete_time=None):
        orders_ids = [order['id'] for order in new_orders]
        if status != 2:
            self.collection.update_many({'_id': {'$in': orders_ids}},
                                        {'$set': {'status': status}})
        else:
            self.collection.update_many({'_id': {'$in': orders_ids}},
                                        {'$set': {'status': status,
                                                  'complete_time': complete_time}})
