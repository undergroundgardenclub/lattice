from sanic import Blueprint, json
import sqlalchemy as sa
from tracking.Event import Event


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_tracking = Blueprint("tracking", url_prefix="v1")


# ROUTES
@blueprint_tracking.route('/tracking/event', methods=['POST'])
async def app_route_intake_recording_series(request):
    session = request.ctx.session
    async with session.begin():
        await session.execute(
            sa.insert(Event).values(request.json.get("event")))
    return json({ "status": "success" })
