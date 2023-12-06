import os

def _env_getter(key):
    # if (os.environ.get(key) == None):
    #     set_secrets_on_env()
    return os.environ.get(key)

# API
def env_get_api_url():
    return _env_getter('API_URL')
def env_get_api_host() -> str:
    return _env_getter('API_HOST')
def env_get_api_port() -> int:
    return int(_env_getter('API_PORT'))

# ASSEMBLY AI
def env_get_assembly_ai_api_key():
    return _env_getter('ASSEMBLY_AI_API_KEY')

# AWS
def env_get_aws_access_key_id():
    return _env_getter('AWS_ACCESS_KEY_ID')
def env_get_aws_secret_access_key():
    return _env_getter('AWS_SECRET_ACCESS_KEY')
def env_get_aws_s3_files_bucket():
    return _env_getter('AWS_FILES_BUCKET')

# ELEVENT LABS
def env_get_eleven_labs_api_key():
    return _env_getter('ELEVENT_LABS_API_KEY')

# ENV
def env_target_service() -> str: # 'api' or 'worker'
    return _env_getter('TARGET_SERVICE')
def env_is_local() -> bool:
    return _env_getter('TARGET_ENV') == 'local'
def env_is_production() -> bool:
    return _env_getter('TARGET_ENV') == 'production'

# HARDWARE/SYSTEM
def env_is_gpu_available() -> bool:
    is_gpu_available = _env_getter('IS_GPU_AVAILABLE') == 'true'
    print(f'INFO (env.py:env_is_gpu_available): is_gpu_available : {is_gpu_available}')
    return is_gpu_available

# OPENAI
def env_get_open_ai_api_key():
    return _env_getter('OPEN_AI_API_KEY')

# QUEUE
def env_queue_host():
    return _env_getter('QUEUE_HOST')
def env_queue_port():
    return _env_getter('QUEUE_PORT')

# SENGRID
def env_get_sendgrid_api_key():
    return _env_getter('SENDGRID_API_KEY')

# # INITIALIZE
# def set_secrets_on_env():
#     # TODO: if we want to do an external secrets fetch