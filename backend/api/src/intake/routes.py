from sanic import Blueprint, json
from intake.jobs.job_intake_query import _job_intake_query
from worker import queue_add_job, queues


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_intake = Blueprint("intake", url_prefix="v1")


# ROUTES
# --- recording series (multiple shorter videos to reduce sync issues, allow for longer runs bc big files will bust raspberry pi processing)
@blueprint_intake.route('/intake/recording/series', methods=['POST'])
async def app_route_intake_recording_series(request):
    # --- start job (skip file to S3, because device has done it already and is sending us keys/urls)
    await queue_add_job(queues['intake_recording_series'], {
        "device_id": request.json.get('device_id'),
        "files": request.json.get('files'),
    })
    # --- respond
    return json({ 'status': 'success' })

# # --- DEPRECATED: recordings (preferring series so we can do longer captures)
# @blueprint_intake.route('/recording', methods=['POST'])
# async def app_route_intake_recording(request):
#     # --- save file to S3 and database. needed for API calls later
#     recording_file_key, recording_file_url = intake_file_preprocessing(request.files.get('file'), "mp4")
#     # --- start job (https://docs.bullmq.io/python/introduction)
#     await queue_add_job(queues['intake_recording'], { "file_key": recording_file_key, "file_url": recording_file_url })
#     # --- respond
#     print("[app_route_intake_recording] responding")
#     return json({ 'status': 'success' })


# --- queries
@blueprint_intake.route('/intake/query', methods=['POST'])
async def app_route_intake_query(request):
    # --- start job
    await queue_add_job(queues['intake_query'], {
        "device_id": request.json.get('device_id'),
        "file": request.json.get("file"),
        "text": request.json.get("text"),
    })
    # --- respond (w/ audio narration response)
    return json({ 'status': 'success' })

