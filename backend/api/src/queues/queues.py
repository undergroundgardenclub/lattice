from bullmq import Queue
from env import env_queue_host, env_queue_port


# SETUP
# --- connection (duplicating from worker to avoid circular import)
queue_redis_opts = dict(host=env_queue_host(),port=env_queue_port())


# QUEUES
queues = dict(
    actor_act=Queue("actor_act", queue_redis_opts),
    actor_action_describe_device_manual=Queue("actor_action_describe_device_manual", queue_redis_opts),
    actor_action_question_answer=Queue("actor_action_question_answer", queue_redis_opts),
    actor_action_recording_annotation=Queue("actor_action_recording_annotation", queue_redis_opts),
    actor_action_recordings_get_clip=Queue("actor_action_recordings_get_clip", queue_redis_opts),
    actor_action_recordings_summarizer=Queue("actor_action_recordings_summarizer", queue_redis_opts),
    device_ingest_recording=Queue("device_ingest_recording", queue_redis_opts),
)
