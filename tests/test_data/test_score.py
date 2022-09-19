"""
`init()` and `run()` are both reserved functions with reserved variables needed to deploy a model, whether it is on ACI or AKS.

`init()` defines how to load the model.

`run()` defines how to handle the datas that are fed to the model from the REST endpoint.
"""
import json

import joblib
import numpy as np
from azureml.core.model import Model


def init():
    """_summary_"""
    global model
    model_path = Model.get_model_path("MODEL_NAME")
    model = joblib.load(model_path)


def run(data):
    """_summary_

    Args:
        data (_type_): _description_

    Returns:
        _type_: _description_
    """
    try:
        data = json.loads(data)
        data = data["data"]
        result = model.predict(np.array(data))
        return result.tolist()
    except Exception as e:
        error = str(e)
        return error
