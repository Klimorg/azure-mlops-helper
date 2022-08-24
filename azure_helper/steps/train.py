import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List

import pandas as pd
from azureml.core import Dataset, Datastore, Run
from azureml.core.model import Model
from skl2onnx import __max_supported_opset__, convert_sklearn
from skl2onnx.common.data_types import FloatTensorType
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score

from azure_helper.logger import get_logger

__here__ = os.path.dirname(__file__)

log = get_logger()


class Train(ABC):
    """Abstract class defining what should be the major steps of a training loop.

    Args:
        ABC (class): Abstract Class
    """

    @abstractmethod
    def get_df_from_datastore_path(self, datastore, datastore_path):
        log.info(f"Loading dataset {datastore_path} from datastore {datastore.name}")
        pass

    @abstractmethod
    def prepare_data(self):
        pass

    @abstractmethod
    def train_model(self):
        log.info("Start training model.")
        pass

    @abstractmethod
    def evaluate_model(self):
        log.info("Start evaluating model.")
        pass

    @abstractmethod
    def save_model(self, model):
        log.info("Saving model to ONNX format.")
        pass

    @abstractmethod
    def register_model(self, model_path):
        pass


class TrainingLoopExample(Train):
    def __init__(
        self,
        run: Run,
        trainig_datastore: str,
        model_name: str,
        target_name: str,
        project_name: str,
    ):
        """Typical example of how you could define a training loop to be used in the `ScriptRunConfig` class in the
        [submit_run][azure_helper.steps.create_aml_experiment.AMLExperiment] method.

        you can use it in the following way.

        ```python
        if __name__ == "__main__":

            run = Run.get_context()
            tl = TrainingLoop(
                run=run,
                trainig_datastore="train_datastore",
                model_name="model_name",
                target_name: "y",
                project_name: "project",
            )
            x_train, y_train, x_test, y_test = tl.prepare_data()

            model = tl.train_model(x_train, y_train)
            tl.evaluate_model(model, x_test, y_test)
            model_path = tl.save_model(model)
            tl.register_model(model_path)
        ```

        Args:
            run (Run): The run corresponding to your Experiment.
            trainig_datastore (str): The name of the datastore where you fetch your datasets.
            model_name (str): The name of the model you train.
            target_name (str): The name of the target, in your dataset.
            project_name (str): The name of the project you're working on.
        """

        self.run = run
        self.model_name = model_name
        self.target_name = target_name
        self.project_name = project_name

        self.workspace = run.experiment.workspace
        self.trainig_datastore = trainig_datastore
        self.datastore = Datastore.get(run.experiment.workspace, trainig_datastore)

    def get_df_from_datastore_path(
        self,
        datastore: Datastore,
        datastore_path: str,
    ) -> pd.DataFrame:
        """Utils function to fetch your datas from a datastore.

        Note that this function is different from [`download_blob_to_df`][azure_helper.utils.blob_storage_interface] method.

        `BlobStorageInterface.download_blob_to_df` takes datas from a blob in one of your container located in your
        storage account. We are fetching datas here from a **datastore**, which is a registered blob in yout AZML workspace.

        Obviously, using `get_df_from_datastore_path` on a Datastore or using `BlobStorageInterface.download_blob_to_df`
        on the blob corresponding to the Datastore will get you the same result.

        Args:
            datastore (Datastore): The name of the registered Datastore in your AZML workspace.
            datastore_path (str): The path to the datas you're fetching.

        Returns:
            The fetched datas as a dataframe.
        """
        # In our example we only have single files,
        # but these may be daily data dumps
        log.info(f"Loading dataset {datastore_path} from datastore {datastore.name}")
        datastore_cfg = [(datastore, datastore_path)]
        dataset = Dataset.Tabular.from_delimited_files(
            path=datastore_cfg,
        )
        return dataset.to_pandas_dataframe()

    def prepare_data(self) -> List[pd.DataFrame]:
        """Get all your datas (train, test) at once.

        Returns:
            List[pd.DataFrame]: Your datas.
        """
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

    def train_model(self, x_train: pd.DataFrame, y_train: pd.DataFrame):
        """Start the training of the model.

        Args:
            x_train (pd.DataFrame): Train dataset.
            y_train (pd.DataFrame): Train target.

        Returns:
            _type_: A trained model.
        """
        log.info("Start training model.")
        model = LogisticRegression()
        model.fit(x_train, y_train)
        return model

    def evaluate_model(self, model, x_test: pd.DataFrame, y_test: pd.DataFrame):
        """Evaluate your model and record the corresponding metric.

        Args:
            model (_type_): The model you want to evaluate.
            x_test (pd.DataFrame): Test/Validation dataset.
            y_test (pd.DataFrame): Test/Validation target.
        """
        log.info("Start evaluating model.")
        y_pred = model.predict(x_test)
        model_f1_score = f1_score(y_test, y_pred)
        self.run.log("F1_Score", model_f1_score)

    def save_model(self, model) -> Path:
        """Convert the model to ONNX and save it.

        Args:
            model (_type_): Your trained model.

        Returns:
            Path: The path where your converted model is located.
        """
        log.info("Saving model to ONNX format.")
        output_dir = Path("outputs")
        output_dir.mkdir(parents=True, exist_ok=True)
        model_path = output_dir / Path("model.onnx")

        initial_types = [("float_input", FloatTensorType([None, model.n_features_in_]))]
        model_onnx = convert_sklearn(
            model,
            initial_types=initial_types,
            target_opset=__max_supported_opset__,
        )

        # Save the model
        with open("outputs/model.onnx", "wb") as f:
            f.write(model_onnx.SerializeToString())
        log.info("Model saved.")
        return model_path

    def register_model(self, model_path: Path):
        """Register your model into your AZML Model Registry.

        Args:
            model_path (Path): The path returned by the function `save_model`.
        """
        self.run.upload_file(str(model_path), "outputs/model.onnx")

        model = self.run.register_model(
            model_name=self.model_name,
            model_path="outputs/model.onnx",
            model_framework=Model.Framework.ONNX,
        )
        self.run.log("Model_ID", model.id)
        log.info(
            f"Model registered with following informations, name : {model.name}, id : {model.id}, version : {model.version}.",
        )
