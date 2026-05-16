from datetime import datetime
from app.models.base import db
from app.models.pickup import PickupTask, PickupItem, PickupStatus
from app.models.order import Order, OrderStatus
from app.models.inventory import ReusableItemTag, TagStatus

VALID_SERVICE_TYPES = ['WASH', 'IRON', 'WASH_IRON', 'DRYCLEAN', 'WASH_FOLD']


def _generate_pickup_number():
    today = datetime.utcnow().strftime('%Y%m%d')
    prefix = f'PKP-{today}-'
    count = PickupTask.query.filter(PickupTask.pickup_number.like(f'{prefix}%')).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


def create_pickup_task(order_id, data):
    order = Order.query.get(order_id)
    if not order:
        return {'error': 'Order not found'}, 404
    if order.status != OrderStatus.CREATED.value:
        return {'error': 'Pickup can only be created for orders in CREATED status'}, 400

    existing = PickupTask.query.filter(
        PickupTask.order_id == order_id,
        PickupTask.status != PickupStatus.CANCELLED.value,
    ).first()
    if existing:
        return {'error': 'An active pickup already exists for this order'}, 409

    pickup = PickupTask(
        pickup_number=_generate_pickup_number(),
        order_id=order_id,
        customer_id=order.customer_id,
        pickup_address=data.get('pickup_address') or order.pickup_address,
        pickup_agent_id=data.get('pickup_agent_id'),
        scheduled_at=data.get('scheduled_at'),
        notes=data.get('notes'),
        status=PickupStatus.ASSIGNED.value if data.get('pickup_agent_id') else PickupStatus.CREATED.value,
    )
    db.session.add(pickup)
    db.session.commit()
    return pickup.to_dict(), 201


def start_pickup(pickup_id):
    pickup = PickupTask.query.get(pickup_id)
    if not pickup:
        return {'error': 'Pickup not found'}, 404
    if pickup.status not in (PickupStatus.CREATED.value, PickupStatus.ASSIGNED.value):
        return {'error': f'Cannot start pickup in status {pickup.status}'}, 400
    pickup.status = PickupStatus.IN_PROGRESS.value
    pickup.started_at = datetime.utcnow()
    db.session.commit()
    return pickup.to_dict(), 200


def add_pickup_item(pickup_id, data):
    """
    Scan a barcode and add it as a garment in this pickup.
    One-time tag: if barcode exists in ReusableItemTag, reuse it.
    If not, create a new permanent tag for this garment.
    """
    pickup = PickupTask.query.get(pickup_id)
    if not pickup:
        return {'error': 'Pickup not found'}, 404
    if pickup.status == PickupStatus.COMPLETED.value:
        return {'error': 'Cannot add items to a completed pickup'}, 400
    if pickup.status == PickupStatus.CANCELLED.value:
        return {'error': 'Cannot add items to a cancelled pickup'}, 400

    if not data.get('barcode'):
        return {'error': 'barcode is required'}, 400
    if not data.get('item_category'):
        return {'error': 'item_category is required'}, 400
    if not data.get('service_type'):
        return {'error': 'service_type is required'}, 400
    if data['service_type'] not in VALID_SERVICE_TYPES:
        return {'error': f"Invalid service_type. Must be one of {VALID_SERVICE_TYPES}"}, 400

    barcode = data['barcode']

    # Reject duplicate scan in same pickup
    if PickupItem.query.filter_by(pickup_id=pickup_id, barcode=barcode).first():
        return {'error': f'Barcode {barcode} already scanned in this pickup'}, 409

    # One-time permanent tag assignment
    tag = ReusableItemTag.query.filter_by(tag_code=barcode).first()
    if not tag:
        order = Order.query.get(pickup.order_id)
        tag = ReusableItemTag(
            tag_code=barcode,
            company_id=order.customer_id if order else None,
            status=TagStatus.IN_USE,
        )
        db.session.add(tag)
        db.session.flush()
    else:
        tag.status = TagStatus.IN_USE

    item = PickupItem(
        pickup_id=pickup_id,
        tag_id=tag.tag_id,
        barcode=barcode,
        item_category=data['item_category'],
        service_type=data['service_type'],
        order_item_id=data.get('order_item_id'),
        notes=data.get('notes'),
    )
    db.session.add(item)
    db.session.commit()
    return item.to_dict(), 201


def complete_pickup(pickup_id, bag_count=None):
    pickup = PickupTask.query.get(pickup_id)
    if not pickup:
        return {'error': 'Pickup not found'}, 404
    if pickup.status != PickupStatus.IN_PROGRESS.value:
        return {'error': 'Pickup must be IN_PROGRESS to complete'}, 400
    if not pickup.pickup_items:
        return {'error': 'Cannot complete pickup with no items scanned'}, 400

    pickup.status = PickupStatus.COMPLETED.value
    pickup.completed_at = datetime.utcnow()
    if bag_count is not None:
        pickup.bag_count = bag_count

    # Auto-advance order to IN_PROCESS
    order = Order.query.get(pickup.order_id)
    if order:
        order.status = OrderStatus.IN_PROCESS.value

    db.session.commit()
    return pickup.to_dict(), 200


def get_pickup(pickup_id):
    pickup = PickupTask.query.get(pickup_id)
    if not pickup:
        return {'error': 'Pickup not found'}, 404
    return pickup.to_dict(), 200
