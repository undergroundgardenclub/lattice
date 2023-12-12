import asyncio
from bullmq import Job, Queue, Worker
from env import env_queue_host, env_queue_port
from intake.jobs.job_intake_recording_series import job_intake_recording_series
from intake.jobs.job_intake_recording_series_done import job_intake_recording_series_done
from intake.jobs.job_intake_query import job_intake_query

# SETUP
# --- connection
redis_opts = dict(host=env_queue_host(),port=env_queue_port())
# --- worker config
# job opts/locks (play with "stall" criteria. jobs being processed that are moved into "stalled" position, that then finish, throw a "lock not found" error)
# read more: https://github.com/OptimalBits/bull/issues/1591#issuecomment-567300561 / https://github.com/OptimalBits/bull/blob/develop/REFERENCE.md#queue / https://github.com/OptimalBits/bull/discussions/2156#discussioncomment-1294458
worker_opts = { "maxStalledCount": 0 }


# QUEUES
queues = dict(
    intake_recording_series=Queue("intake_recording_series", redis_opts),
    intake_recording_series_done=Queue("intake_recording_series_done", redis_opts),
    intake_query=Queue("intake_query", redis_opts),
)


# FUNCS
# --- process wrapper (for logging ease)
def pw(processor_fn):
    def _pw(job, job_token):
        print("[worker] job: ", job.id)
        return processor_fn(job, job_token)
    return _pw
# --- job add wrapper (for closing + remove on fail config ease)
async def queue_add_job(queue, job_data: dict, job_opts: dict = {}) -> Job:
    print(f'[queue_add] {queue.name} ->', job_data)
    job = await queue.add(queue.name, job_data, { "removeOnComplete": True, "removeOnFail": True, **job_opts })
    await queue.close()
    return job


# WORK
async def work():
    # --- intake recording
    w_intake_recording_series = Worker("intake_recording_series", pw(job_intake_recording_series), { **worker_opts, "connection": redis_opts, "lockDuration": 1000 * 60 * 5 }) # 5 min job lock allowed (default is 30 seconds). should override per queue
    w_intake_recording_series_done = Worker("intake_recording_series_done", pw(job_intake_recording_series_done), { **worker_opts, "connection": redis_opts, "lockDuration": 1000 * 60 * 5 }) # 5 min job lock allowed (default is 30 seconds). should override per queue
    # --- intake query
    w_intake_query = Worker("intake_query", pw(job_intake_query), { **worker_opts, "connection": redis_opts, "lockDuration": 1000 * 60 * 5 }) # 5 min job lock allowed (default is 30 seconds). should override per queue
    # ... keep workers alive
    while True:
        await asyncio.sleep(1)

# --- run
def start_worker():
    asyncio.run(work())