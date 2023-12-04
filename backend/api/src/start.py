import torch
from api import start_api

# CONFIG
# Restrict PyTorch Processor Usage (blocks other processors):
# https://github.com/UKPLab/sentence-transformers/issues/1318
# https://github.com/pytorch/pytorch/issues/36191#issuecomment-620956849
torch.set_num_threads(1)

# INIT
# Maybe one day we multiprocess api/workers
if __name__ == "__main__":
    print("INFO (start.py) start")
    start_api()