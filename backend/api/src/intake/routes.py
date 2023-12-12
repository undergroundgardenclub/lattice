from sanic import Blueprint, json
from intake.jobs.job_intake_query import _job_intake_query
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

# --- recording series: v2 -- signal done so we can compile summary file
@blueprint_intake.route('/intake/recording/series/done', methods=['POST'])
async def app_route_intake_recording_series_done(request):
    await queue_add_job(queues['intake_recording_series_done'], {
        "device_id": request.json.get('device_id'),
        "series_id": request.json.get('series_id'),
    }, {
        "delay": 1000 * 0 # delaying to ensure final recording series is transcribed/saved. avoids device having to manage a race condition
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

