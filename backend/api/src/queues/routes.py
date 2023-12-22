from sanic import Blueprint, json
from queues.queues import queues
from queues.queue_add_job import queue_add_job


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_queues = Blueprint("queues", url_prefix="v1")


# ROUTES
@blueprint_queues.route('/queue/<queue_name>', methods=['POST'])
async def app_route_queue_post(request, queue_name):
    print(f"[app_route_queue_post] queue job: {queue_name}", request.json)
    await queue_add_job(queues[queue_name], request.json)
    return json({ 'status': 'success' })
