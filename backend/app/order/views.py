from datetime import datetime
from app.models.base import db
from app.models.order import Order, OrderItem, OrderStatus

VALID_SERVICE_TYPES = ['WASH', 'IRON', 'WASH_IRON', 'DRYCLEAN', 'WASH_FOLD']
VALID_STATUSES = [s.value for s in OrderStatus]


def _generate_order_number():
    today = datetime.utcnow().strftime('%Y%m%d')
    prefix = f'ORD-{today}-'
    count = Order.query.filter(Order.order_number.like(f'{prefix}%')).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


def create_order(data, created_by_id):
    if not data.get('customer_id'):
        return {'error': 'customer_id is required'}, 400
    if not data.get('pickup_address'):
        return {'error': 'pickup_address is required'}, 400
    if not data.get('items'):
        return {'error': 'At least one item is required'}, 400

    for item in data['items']:
        if not item.get('item_category') or not item.get('service_type'):
            return {'error': 'Each item needs item_category and service_type'}, 400
        if item['service_type'] not in VALID_SERVICE_TYPES:
            return {'error': f"Invalid service_type: {item['service_type']}. Must be one of {VALID_SERVICE_TYPES}"}, 400

    order = Order(
        order_number=_generate_order_number(),
        customer_id=data['customer_id'],
        created_by=created_by_id,
        pickup_address=data['pickup_address'],
        delivery_address=data.get('delivery_address'),
        warehouse_id=data.get('warehouse_id'),
        notes=data.get('notes'),
        status=OrderStatus.CREATED.value,
    )
    db.session.add(order)
    db.session.flush()

    for item_data in data['items']:
        item = OrderItem(
            order_id=order.order_id,
            item_category=item_data['item_category'],
            service_type=item_data['service_type'],
            quantity=item_data.get('quantity', 1),
        )
        db.session.add(item)

    db.session.commit()
    return order.to_dict(), 201


def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return {'error': 'Order not found'}, 404
    return order.to_dict(), 200


def get_all_orders(customer_id=None, status=None):
    q = Order.query
    if customer_id:
        q = q.filter_by(customer_id=customer_id)
    if status:
        q = q.filter_by(status=status.upper())
    orders = q.order_by(Order.created_at.desc()).all()
    return [o.to_dict() for o in orders], 200


def update_order_status(order_id, new_status):
    order = Order.query.get(order_id)
    if not order:
        return {'error': 'Order not found'}, 404
    if new_status not in VALID_STATUSES:
        return {'error': f'Invalid status. Must be one of: {VALID_STATUSES}'}, 400
    order.status = new_status
    db.session.commit()
    return order.to_dict(), 200
