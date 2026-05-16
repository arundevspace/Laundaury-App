from datetime import datetime
from app.models.base import db
from app.models.inward import Inward, InwardItem
from app.models.pickup import PickupTask, PickupItem, PickupStatus
from app.models.inventory import ReusableItemTag


def _generate_inward_number():
    today = datetime.utcnow().strftime('%Y%m%d')
    prefix = f'INW-{today}-'
    count = Inward.query.filter(Inward.inward_number.like(f'{prefix}%')).count()
    return f'{prefix}{str(count + 1).zfill(4)}'


def create_inward(data, operator_user_id):
    if not data.get('pickup_id') or not data.get('warehouse_id'):
        return {'error': 'pickup_id and warehouse_id are required'}, 400

    pickup = PickupTask.query.get(data['pickup_id'])
    if not pickup:
        return {'error': 'Pickup not found'}, 404
    if pickup.status != PickupStatus.COMPLETED.value:
        return {'error': 'Pickup must be COMPLETED before inwarding'}, 400

    existing = Inward.query.filter_by(pickup_id=pickup.pickup_id, is_completed=False).first()
    if existing:
        return {'error': 'An open inward already exists for this pickup', 'inward_id': existing.inward_id}, 409

    inward = Inward(
        inward_number=_generate_inward_number(),
        pickup_id=pickup.pickup_id,
        warehouse_id=data['warehouse_id'],
        inwarded_by=operator_user_id,
        total_items_expected=len(pickup.pickup_items),
        notes=data.get('notes'),
    )
    db.session.add(inward)
    db.session.commit()
    return inward.to_dict(), 201


def scan_inward_item(inward_id, barcode, condition_notes=None, is_received=True):
    inward = Inward.query.get(inward_id)
    if not inward:
        return {'error': 'Inward not found'}, 404
    if inward.is_completed:
        return {'error': 'Inward is already completed'}, 400

    if InwardItem.query.filter_by(inward_id=inward_id, barcode=barcode).first():
        return {'error': f'Barcode {barcode} already scanned in this inward'}, 409

    tag = ReusableItemTag.query.filter_by(tag_code=barcode).first()
    pickup_item = PickupItem.query.filter_by(
        pickup_id=inward.pickup_id, barcode=barcode
    ).first()

    inward_item = InwardItem(
        inward_id=inward_id,
        barcode=barcode,
        tag_id=tag.tag_id if tag else None,
        pickup_item_id=pickup_item.pickup_item_id if pickup_item else None,
        condition_notes=condition_notes,
        is_received=is_received,
    )
    db.session.add(inward_item)

    if is_received:
        inward.total_items_received = (inward.total_items_received or 0) + 1

    db.session.commit()

    result = inward_item.to_dict()
    result['expected'] = pickup_item is not None
    result['items_received'] = inward.total_items_received
    result['items_expected'] = inward.total_items_expected
    return result, 201


def complete_inward(inward_id):
    inward = Inward.query.get(inward_id)
    if not inward:
        return {'error': 'Inward not found'}, 404
    if inward.is_completed:
        return {'error': 'Inward is already completed'}, 400

    inward.is_completed = True
    inward.inwarded_at = datetime.utcnow()
    db.session.commit()

    result = inward.to_dict()
    result['missing_items'] = inward.total_items_expected - inward.total_items_received
    return result, 200


def get_inward(inward_id):
    inward = Inward.query.get(inward_id)
    if not inward:
        return {'error': 'Inward not found'}, 404
    return inward.to_dict(), 200


def list_inwards(warehouse_id=None, completed=None):
    q = Inward.query
    if warehouse_id:
        q = q.filter_by(warehouse_id=warehouse_id)
    if completed is not None:
        q = q.filter_by(is_completed=completed)
    inwards = q.order_by(Inward.created_at.desc()).all()
    return [i.to_dict() for i in inwards], 200
