from sanic import Blueprint, json
from uuid import uuid4

from emails.send_email import send_email
from emails.fill_email_template_html import fill_email_template_html_tasks_summary
from file.file_cloud_storage import get_stored_file_bytes, get_stored_file_url, store_file_from_pyfile
from file.file_utils import tmp_file_rmv, tmp_file_set
from llms.prompts import prompt_recording_transcript_to_task_headers, prompt_recording_transcript_to_task_outline
from voice.speech_to_text import speech_to_text
from vision.cv import video_frame_at_second


# BLUEPRINT: aka route prefixing/reference class we attach to the api
blueprint_intake = Blueprint("intake", url_prefix="v1/intake")


# ROUTES
@blueprint_intake.route('/recording', methods=['GET', 'POST'])
async def app_route_intake_recording(request):
    # --- save file to S3 and database. needed for API calls later
    # recording_file_key, recording_file_url = intake_file_preprocessing(request.files.get('file'))
    recording_file_key = "ee81aede-315c-41c3-95f9-cb6b421d6198.mp4"
    recording_file_url = get_stored_file_url(recording_file_key)

    # --- start job (https://docs.bullmq.io/python/introduction)
    await queue_add_job(queues['intake_recording'], { "file_key": recording_file_key, "file_url": recording_file_url })

    # --- respond
    return json({ 'status': 'success' })
