import requests
import numpy as np
import time
import os

AGGREGATOR_URL = os.getenv("AGGREGATOR_URL")

# Fake local training
local_weights = np.random.rand(5)

print("Training locally...")
time.sleep(2)

# Send update
response = requests.post(
    f"{AGGREGATOR_URL}/submit",
    json={"weights": local_weights.tolist()}
)

print("Sent update:", response.json())