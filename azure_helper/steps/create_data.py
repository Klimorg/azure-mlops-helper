import pandas as pd

from azure_helper.interfaces.blob_storage_interface import BlobStorageInterface


class CreateData:
    def __init__(
        self,
        project_name: str,
        train_datastore: str = "train",
        test_datastore: str = "test",
    ):
        """This class is just a wrapper around the [BlobStorageInterface][azure_helper.utils.blob_storage_interface] and
        might disappear, as it is not really needed.

        Args:
            project_name (str): _description_
            train_datastore (str, optional): _description_. Defaults to "train".
            test_datastore (str, optional): _description_. Defaults to "test".
        """
        self.project_name = project_name
        self.train_datastore = train_datastore
        self.test_datastore = test_datastore

    def upload_training_data(
        self,
        blob_storage_interface: BlobStorageInterface,
        x_train: pd.DataFrame,
        y_train: pd.DataFrame,
    ):
        """Upload datas to the training blob storage.

        Args:
            blob_storage_interface (BlobStorageInterface): The interface with your storage account.
            x_train (pd.DataFrame): Train datas.
            y_train (pd.DataFrame): Train datas.
        """
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
        """Upload datas to the validation blob storage.

        Args:
            blob_storage_interface (BlobStorageInterface): The interface with your storage account.
            x_valid (pd.DataFrame): Validation datas.
            y_valid (pd.DataFrame): Validation datas.
        """
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
        """Upload datas to the test blob storage.

        Args:
            blob_storage_interface (BlobStorageInterface): The interface with your storage account.
            x_test (pd.DataFrame): Test datas.
            y_test (pd.DataFrame): Test datas.
        """
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
