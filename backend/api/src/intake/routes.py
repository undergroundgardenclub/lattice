from sanic import Blueprint, json
from file.file_cloud_storage import get_stored_file_url
from intake.intake_file_preprocessing import intake_file_preprocessing
from intake.jobs.job_intake_query import _job_intake_query
from worker import queue_add_job, queues


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_intake = Blueprint("intake", url_prefix="v1/intake")


# ROUTES
# --- recordings
@blueprint_intake.route('/recording', methods=['POST'])
async def app_route_intake_recording(request):
    # --- save file to S3 and database. needed for API calls later
    recording_file_key, recording_file_url = intake_file_preprocessing(request.files.get('file'))
    # --- start job (https://docs.bullmq.io/python/introduction)
    await queue_add_job(queues['intake_recording'], { "file_key": recording_file_key, "file_url": recording_file_url })
    # --- respond
    return json({ 'status': 'success' })

# added GET for ease of trigger/testing
@blueprint_intake.route('/recording', methods=['GET'])
async def app_route_intake_recording_test(request):
    recording_file_key = "ee81aede-315c-41c3-95f9-cb6b421d6198.mp4"
    recording_file_url = get_stored_file_url(recording_file_key)
    await queue_add_job(queues['intake_recording'], { "file_key": recording_file_key, "file_url": recording_file_url })
    return json({ 'status': 'success' })

# --- TODO: sessions (aka chunked recordings part of a longer session, means i think we need a start/stop w/ server)

# --- queries
@blueprint_intake.route('/query', methods=['POST'])
async def app_route_intake_query(request):
    # --- save file to S3 and database. needed for API calls later
    recording_file_key, recording_file_url = intake_file_preprocessing(request.files.get('file'))
    # --- start job (TODO: switch to queue when we can access job data when they're finished)
    job = await queue_add_job(queues['intake_query'], { "file_key": recording_file_key, "file_url": recording_file_url })
    # --- respond
    return json({ 'status': 'success', 'data': { 'file_url': job.data['file_url'] } })

