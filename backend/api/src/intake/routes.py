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
    recording_file_key, recording_file_url = intake_file_preprocessing(request.files.get('file'), "mp4")
    # --- start job (https://docs.bullmq.io/python/introduction)
    await queue_add_job(queues['intake_recording'], { "file_key": recording_file_key, "file_url": recording_file_url })
    # --- respond
    print("[app_route_intake_recording] responding")
    return json({ 'status': 'success' })

# added GET for ease of trigger/testing
@blueprint_intake.route('/recording', methods=['GET'])
async def app_route_intake_recording_test(request):
    recording_file_key = "03f97535-8d59-401f-b57d-3c54ea80030f.mp4"
    recording_file_url = get_stored_file_url(recording_file_key)
    await queue_add_job(queues['intake_recording'], { "file_key": recording_file_key, "file_url": recording_file_url })
    return json({ 'status': 'success' })

# --- TODO: sessions (aka chunked recordings part of a longer session, means i think we need a start/stop w/ server)

# --- queries
@blueprint_intake.route('/query', methods=['POST'])
async def app_route_intake_query(request):
    # --- save file to S3 and database. needed for API calls later
    recording_file_key, recording_file_url = intake_file_preprocessing(request.files.get('file'), "mp4")
    # --- start job
    # job = await queue_add_job(queues['intake_query'], { "file_key": recording_file_key, "file_url": recording_file_url })
    # job_data = job.data
    job_data = await _job_intake_query(recording_file_key, recording_file_url)
    # --- respond
    print("[app_route_intake_query] responding")
    return json({ 'status': 'success', 'data': { 'file_url': job_data['file_url'] } })

