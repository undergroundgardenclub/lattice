import asyncio
from bullmq import Job, Queue, Worker
from env import env_queue_host, env_queue_port
from actor.pf_actor_act import pf_actor_act
from actor.actions.describe_device_manual.pf_actor_action_device_manual import pf_actor_action_describe_device_manual
from actor.actions.question_answer.pf_actor_action_question_answer import pf_actor_action_question_answer
from actor.actions.recordings_get_clip.pf_actor_action_recordings_get_clip import pf_actor_action_recordings_get_clip
from actor.actions.recordings_summarize.pf_actor_action_recordings_summarizer import pf_actor_action_recordings_summarizer
from device.ingest.pf_device_ingest_recording import pf_device_ingest_recording


# SETUP
# --- connection (duplicating from queues toa avoid circular import)
queue_redis_opts = dict(host=env_queue_host(),port=env_queue_port())
# --- worker config
# job opts/locks (play with "stall" criteria. jobs being processed that are moved into "stalled" position, that then finish, throw a "lock not found" error)
# read more: https://github.com/OptimalBits/bull/issues/1591#issuecomment-567300561 / https://github.com/OptimalBits/bull/blob/develop/REFERENCE.md#queue / https://github.com/OptimalBits/bull/discussions/2156#discussioncomment-1294458
# lock durations default to 30 seconds, extend if long running jobs
queue_worker_opts = { "connection": queue_redis_opts, "maxStalledCount": 0 }


# WORK
# --- process function wrapper (for logging ease)
def pfw(processor_fn):
    def _pfw(job, job_token):
        print("[worker] job: ", job.id)
        return processor_fn(job, job_token)
    return _pfw

async def work():
    # --- actors
    w_actor_act = Worker("actor_act", pfw(pf_actor_act), { **queue_worker_opts })
    w_actor_action_describe_device_manual = Worker("actor_action_describe_device_manual", pfw(pf_actor_action_describe_device_manual), { **queue_worker_opts, "lockDuration": 1000 * 60 * 2 })
    w_actor_action_question_answer = Worker("actor_action_question_answer", pfw(pf_actor_action_question_answer), { **queue_worker_opts, "lockDuration": 1000 * 60 * 2 })
    w_actor_action_recordings_get_clip = Worker("actor_action_recordings_get_clip", pfw(pf_actor_action_recordings_get_clip), { **queue_worker_opts, "lockDuration": 1000 * 60 * 15 })
    w_actor_action_recordings_summarizer = Worker("actor_action_recordings_summarizer", pfw(pf_actor_action_recordings_summarizer), { **queue_worker_opts, "lockDuration": 1000 * 60 * 15 })
    # --- devices
    w_device_ingest_recording = Worker("device_ingest_recording", pfw(pf_device_ingest_recording), { **queue_worker_opts })
    # ... keep workers alive
    while True:
        await asyncio.sleep(1)

# --- run
def start_worker():
    asyncio.run(work())
