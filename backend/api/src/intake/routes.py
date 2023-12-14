from sanic import Blueprint, json
from worker import queue_add_job, queues


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_intake = Blueprint("intake", url_prefix="v1")


# ROUTES
# --- recording series: v2
@blueprint_intake.route('/intake/recording/series', methods=['POST'])
async def app_route_intake_recording_series(request):
    await queue_add_job(queues['intake_recording_series'], {
        "device_id": request.json.get('device_id'),
        "series_id": request.json.get('series_id'),
        "file": request.json.get('file'), # recording file url/key
    })
    return json({ 'status': 'success' })

# --- queries
@blueprint_intake.route('/intake/query', methods=['POST'])
async def app_route_intake_query(request):
    await queue_add_job(queues['intake_query'], {
        "device_id": request.json.get('device_id'),
        "series_id": request.json.get('series_id'),
        "file": request.json.get("file"),
        "text": request.json.get("text"), # optional, mostly for local dev testing
    })
    return json({ 'status': 'success' })
