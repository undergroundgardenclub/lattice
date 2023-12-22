from bullmq import Job, Queue, Worker


# --- job add wrapper (for closing + remove on fail config ease)
async def queue_add_job(queue, job_data: dict, job_opts: dict = {}) -> Job:
    print(f'[queue_add] {queue.name} ->', job_data)
    job = await queue.add(queue.name, job_data, { "removeOnComplete": True, "removeOnFail": True, **job_opts })
    await queue.close()
    return job