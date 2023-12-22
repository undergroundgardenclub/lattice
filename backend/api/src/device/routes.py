from datetime import datetime
from sanic import Blueprint, json
import sqlalchemy as sa
from device.DeviceMessage import DeviceMessage
from orm import serialize
from queues.queues import queues
from queues.queue_add_job import queue_add_job


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_devices = Blueprint("devices", url_prefix="v1")


# ROUTES
# --- intake
@blueprint_devices.route('/device/ingest/recording', methods=['POST'])
async def app_route_device_ingest_recording(request):
    await queue_add_job(queues['device_ingest_recording'], {
        "device_id": request.json.get('device_id'),
        "series_id": request.json.get('series_id'),
        "media_file_dict": request.json.get('media_file_dict'), # recording file url/key
    })
    return json({ 'status': 'success' })

# --- device messages queue (ex: for getting playback)
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
