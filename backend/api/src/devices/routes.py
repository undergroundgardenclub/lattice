from datetime import datetime
from sanic import Blueprint, json
import sqlalchemy as sa
from devices.DeviceMessage import DeviceMessage
from orm import serialize


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_devices = Blueprint("devices", url_prefix="v1")


# ROUTES
# --- device messages queue
@blueprint_devices.route('/device/messages', methods=['GET'])
async def app_route_device_messages(request):
    device_id = request.json.get('device_id')
    session = request.ctx.session
    async with session.begin():
        print(f"[app_route_device_messages] lookup -> {device_id}")
        # --- query for messages
        query_device_messages = await session.execute(
            sa.select(DeviceMessage).where(
                sa.and_(DeviceMessage.device_id == str(device_id), DeviceMessage.delivered_at == None)
            ))
        dms = query_device_messages.scalars().unique().all()
        # --- set as "delivered" so we don't server them again (commits when we leave "begin" context)
        for dm in dms:
            dm.delivered_at = datetime.now()
            session.add(dm)
    # --- respond
    return json({ 'status': 'success', "data": { "messages": serialize(dms) } })

