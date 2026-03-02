from fastapi import FastAPI
from pydantic import BaseModel
import numpy as np

app = FastAPI()

global_weights = None
client_updates = []

class Weights(BaseModel):
    weights: list

@app.post("/submit")
def submit_update(data: Weights):
    global client_updates
    client_updates.append(np.array(data.weights))
    return {"message": "Update received"}

@app.get("/aggregate")
def aggregate():
    global global_weights, client_updates

    if len(client_updates) == 0:
        return {"message": "No updates yet"}

    global_weights = np.mean(client_updates, axis=0)
    client_updates = []

    return {"global_weights": global_weights.tolist()}

@app.get("/get_global")
def get_global():
    if global_weights is None:
        return {"message": "No global model yet"}
    return {"global_weights": global_weights.tolist()}