# import torch
from api import start_api
from worker import start_worker
from env import env_target_service

# CONFIG
# Restrict PyTorch Processor Usage (blocks other processors):
# https://github.com/UKPLab/sentence-transformers/issues/1318
# https://github.com/pytorch/pytorch/issues/36191#issuecomment-620956849
# torch.set_num_threads(1)

# INIT
# Maybe one day we multiprocess api/workers
if __name__ == "__main__":
    service = env_target_service()
    print("[start] service: ", service)
    # --- worker api (using bull, not sanic's worker system so workers can use other languages)
    if service == 'worker_api':
        start_worker()
    # --- api
    if service == 'api':
        start_api()
