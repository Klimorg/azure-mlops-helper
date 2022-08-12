import os
from abc import ABC, abstractmethod
from pathlib import Path

from azureml.core import Dataset, Datastore, Run
from azureml.core.model import Model
from skl2onnx import __max_supported_opset__, convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

from azure_helper.logger import get_logger
from azure_helper.utils.transform_data import remove_collinear_cols

__here__ = os.path.dirname(__file__)

log = get_logger()


class Train(ABC):
    @abstractmethod
    def get_df_from_datastore_path(self, datastore, datastore_path):
        log.info(f"Loading dataset {datastore_path} from datastore {datastore.name}")
        pass

    @abstractmethod
    def prepare_data(self):
        pass

    def train_model(self):
        log.info("Start training model.")
        pass

    def evaluate_model(self):
        log.info("Start evaluating model.")
        pass

    def save_model(self, model):
        log.info("Saving model to ONNX format.")
        pass

    def register_model(self, model_path):
        pass


class TrainingLoop(Train):
    def __init__(
        self,
        run: Run,
        trainig_datastore: str,
        model_name: str,
        target_name: str,
        project_name: str,
    ):

        self.run = run
        self.model_name = model_name
        self.target_name = target_name
        self.project_name = project_name

        self.workspace = run.experiment.workspace
        self.trainig_datastore = trainig_datastore
        self.datastore = Datastore.get(run.experiment.workspace, trainig_datastore)

    def get_df_from_datastore_path(self, datastore, datastore_path):
        # In our example we only have single files,
        # but these may be daily data dumps
        log.info(f"Loading dataset {datastore_path} from datastore {datastore.name}")
        datastore_path = [(datastore, datastore_path)]
        dataset = Dataset.Tabular.from_delimited_files(
            path=datastore_path,
        )
        return dataset.to_pandas_dataframe()

    def prepare_data(self):
        x_train = self.get_df_from_datastore_path(
            self.datastore,
            f"{self.project_name}/train/X_train.csv",
        )

        y_train = self.get_df_from_datastore_path(
            self.datastore,
            f"{self.project_name}/train/y_train.csv",
        )
        y_train = y_train[self.target_name]

        x_test = self.get_df_from_datastore_path(
            self.datastore,
            f"{self.project_name}/test/X_test.csv",
        )

        y_test = self.get_df_from_datastore_path(
            self.datastore,
            f"{self.project_name}/test/y_test.csv",
        )
        y_test = y_test[self.target_name]

        return x_train, y_train, x_test, y_test

    def train_model(self, x_train, y_train):
        log.info("Start training model.")
        model = LogisticRegression()
        model.fit(x_train, y_train)
        return model

    def evaluate_model(self, model, x_test, y_test):
        log.info("Start evaluating model.")
        y_pred = model.predict(x_test)
        model_f1_score = f1_score(y_test, y_pred)
        self.run.log("F1_Score", model_f1_score)

    def save_model(self, model):
        log.info("Saving model to ONNX format.")
        output_dir = __here__ / Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        # output_dir = os.path.join(__here__, "outputs")
        # os.makedirs(output_dir, exist_ok=True)
        model_path = output_dir / Path("model.onnx")
        # model_path = os.path.join(output_dir, "model.pkl")

        initial_types = [("float_input", FloatTensorType([None, model.n_features_in_]))]
        model_onnx = convert_sklearn(
            model,
            initial_types=initial_types,
            target_opset=__max_supported_opset__,
        )

        # Save the model
        with open("azure_helper/steps/outputs/model.onnx", "wb") as f:
            f.write(model_onnx.SerializeToString())
        # joblib.dump(model, model_path)
        log.info("Model saved.")
        return model_path

    def register_model(self, model_path):
        self.run.upload_file(str(model_path), "azure_helper/steps/outputs/model.onnx")

        model = self.run.register_model(
            model_name=self.model_name,
            model_path="azure_helper/steps/outputs/model.onnx",
            model_framework=Model.Framework.ONNX,
        )
        self.run.log("Model_ID", model.id)
        log.info(
            f"Model registered with following informations, name : {model.name}, id : {model.id}, version : {model.version}.",
        )
