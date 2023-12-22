from sanic import Blueprint, json
from queues.queues import queues
from queues.queue_add_job import queue_add_job


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_actor = Blueprint("actor", url_prefix="v1")


# ROUTES
@blueprint_actor.route('/actor/act', methods=['POST'])
async def app_route_actor_act(request):
    """
    Generalist entry point for media/text queries that should do something
    """
    await queue_add_job(queues['actor_act'], {
        "device_id": request.json.get('device_id'),
        "series_id": request.json.get('series_id'),
        # --- query data that is either or
        "query_media_file_dict": request.json.get("media_file_dict"),
        "query_text": request.json.get("text"),
    })
    return json({ 'status': 'success' })
