"""init() and run(data) are both reserved functions with reserved variables needed to deploy a model, whether it is on ACI or AKS.

init() defines how to laod the model.

run(data) defines how to handle the datas that are fed to the model from the REST endpoint.
"""
# import json

# import joblib
# import numpy as np
# from azureml.core.model import Model

# from azure_helper.utils.const import MODEL_NAME


# def init():
#     global model
#     model_path = Model.get_model_path(MODEL_NAME)
#     model = joblib.load(model_path)


# def run(data):
#     try:
#         data = json.loads(data)
#         data = data["data"]
#         result = model.predict(np.array(data))
#         return result.tolist()
#     except Exception as e:
#         error = str(e)
#         return error
