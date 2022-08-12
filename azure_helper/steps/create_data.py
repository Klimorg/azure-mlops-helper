import pandas as pd

from azure_helper.utils.aml_interface import AMLInterface
from azure_helper.utils.blob_storage_interface import BlobStorageInterface


class CreateData:
    def __init__(
        self,
        project_name: str,
        train_datastore: str = "train",
        test_datastore: str = "test",
    ):
        self.project_name = project_name
        self.train_datastore = train_datastore
        self.test_datastore = test_datastore

    def upload_training_data(
        self,
        blob_storage_interface: BlobStorageInterface,
        x_train: pd.DataFrame,
        y_train: pd.DataFrame,
    ):
        blob_storage_interface.upload_df_to_blob(
            dataframe=x_train,
            container_name=f"{self.project_name}",
            blob_path=f"{self.train_datastore}/X_train.csv",
        )
        blob_storage_interface.upload_df_to_blob(
            dataframe=y_train,
            container_name=f"{self.project_name}",
            blob_path=f"{self.train_datastore}/y_train.csv",
        )

    def upload_validation_data(
        self,
        blob_storage_interface: BlobStorageInterface,
        x_valid: pd.DataFrame,
        y_valid: pd.DataFrame,
    ):
        # Data to be used during model validation
        blob_storage_interface.upload_df_to_blob(
            dataframe=x_valid,
            container_name=f"{self.project_name}",
            blob_path=f"{self.train_datastore}/X_valid.csv",
        )
        blob_storage_interface.upload_df_to_blob(
            dataframe=y_valid,
            container_name=f"{self.project_name}",
            blob_path=f"{self.train_datastore}/y_valid.csv",
        )

    def upload_test_data(
        self,
        blob_storage_interface: BlobStorageInterface,
        x_test: pd.DataFrame,
        y_test: pd.DataFrame,
    ):
        # Data to be used during model evaluation
        # So stored in the training container
        blob_storage_interface.upload_df_to_blob(
            dataframe=x_test,
            container_name=f"{self.project_name}",
            blob_path=f"{self.test_datastore}/X_test.csv",
        )
        blob_storage_interface.upload_df_to_blob(
            dataframe=y_test,
            container_name=f"{self.project_name}",
            blob_path=f"{self.test_datastore}/y_test.csv",
        )
