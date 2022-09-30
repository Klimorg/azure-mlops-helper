from io import StringIO

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from azure_helper.logger import get_logger

log = get_logger()


class BlobStorageInterface:
    def __init__(self, storage_acct_name: str, storage_acct_key: str):
        """Class responsible to interact with an existing Azure Storage Account.

        It uses a connection string to connect to the Storage Account.

        ```python
        conn_str = (
            "DefaultEndpointsProtocol=https;"
            + f"AccountName={storage_acct_name};"
            + f"AccountKey={storage_acct_key};"
            + "EndpointSuffix=core.windows.net"
        )
        ```

        !!! info "Information"

            To get the key of this storage account we use the following command with the azure-cli.

            ```sh
            az storage account keys list --account-name <storage-account-name> --resource-group <resource-group>
            ```

        This class is responsible for :

        * Creating a container in the storage account.
        * Uploading a dataframe (as a `csv` for now) inside a blob in one of the container of the storage account.
        * Download a `csv` from a blob in one of the container of the storage account and render it as a pandas dataframe.

        Args:
            storage_acct_name (str): The name of the storage account to which you want to connect.
            storage_acct_key (str): The account key of the storage account.
        """
        conn_str = (
            "DefaultEndpointsProtocol=https;"
            + f"AccountName={storage_acct_name};"
            + f"AccountKey={storage_acct_key};"
            + "EndpointSuffix=core.windows.net"
        )
        self.blob_service_client = BlobServiceClient.from_connection_string(
            conn_str,
        )

    def create_container(self, container_name: str):
        """Create a container inside the storage account.

        Args:
            container_name (str): the name of the container you want to create. This name can only contains
                alphanumeric numbers and dashes '-'.
        """
        try:
            self.blob_service_client.create_container(container_name)
            log.info(f"Creating blob storage container {container_name}.")
        except ResourceExistsError:
            log.warning(f"Blob storage container {container_name} already exists.")
            pass

    def upload_to_blob(
        self,
        dataset,
        container_name: str,
        blob_path: str,
    ):
        """Upload a dataset file inside a blob.

        Eg the following code.


        ```python
        from azure_helper.utils.blob_storage_interface import BlobStorageInterface

        blob_storage_interface = BlobStorageInterface(
            storage_acct_name="workspaceperso5448820782",
            storage_acct_key="XXXXX-XXXX-XXXXX-XXXX",
            )

        dataset = dataframe.to_csv(index=False, header=True).encode()

        blob_storage_interface.upload_to_blob(
            dataset=dataset,
            container_name="project-mlops-mk-5448820782",
            blob_path="raw/data.csv",
        )
        ```

        Upload the dataframe `dataframe`as `raw.csv`in the following way.


        ```bash
        Storage_Account : workspaceperso5448820782
            │
            ├── Container : project-mlops-mk-5448820782
            │   ├── blob : raw
            │   │           └── data.csv
            │   └── blob : test
        ```

        !!! attention "Attention"

            As of now, there is no **data versioning**. Meaning that if the `blob_path` already exists, it will be
            overwritten with new datas.


        Args:
            dataset (Any): The datas you want to upload.
            container_name (str): The name of the container on which you want to upload the dataframe.
            blob_path (str): The path to the csv
        """
        self.create_container(container_name)

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_path,
        )

        try:
            blob_client.upload_blob(dataset)
            log.info(f"Dataset uploaded at blob path : {blob_path}.")
        except ResourceExistsError:
            log.warning(
                f"Blob path {blob_path} already contains datas. Now deleting old datas tu upload the new ones.",
            )
            blob_client.delete_blob()
            blob_client.upload_blob(dataset)
            log.info(f"New dataset uploaded at blob path : {blob_path}.")

    def upload_df_to_blob(
        self,
        dataframe: pd.DataFrame,
        container_name: str,
        blob_path: str,
    ):
        """Upload a pandas dataframe as a `csv` file inside a blob.

        Eg the following code.


        ```python
        from azure_helper.utils.blob_storage_interface import BlobStorageInterface

        blob_storage_interface = BlobStorageInterface(
            storage_acct_name="workspaceperso5448820782",
            storage_acct_key="XXXXX-XXXX-XXXXX-XXXX",
            )

        blob_storage_interface.upload_df_to_blob(
            dataframe=x_train,
            container_name="project-mlops-mk-5448820782",
            blob_path="train/x_train.csv",
        )
        blob_storage_interface.upload_df_to_blob(
            dataframe=x_train,
            container_name="project-mlops-mk-5448820782",
            blob_path="train/y_train.csv",
        )
        ```

        Upload the dataframes `x_train` and `y_train` as `x_train.csv` and `y_train.csv` in the following way.


        ```bash
        Storage_Account : workspaceperso5448820782
            │
            ├── Container : project-mlops-mk-5448820782
            │   ├── blob : train
            │   │           ├── x_train.csv
            │   │           └── y_train.csv
            │   └── blob : test
        ```

        !!! attention "Attention"

            As of now, there is no **data versioning**. Meaning that if the `blob_path` already exists, it will be
            overwritten with new datas.


        Args:
            dataframe (pd.DataFrame): The dataframe you want to upload.
            container_name (str): The name of the container on which you want to upload the dataframe.
            blob_path (str): The path to the csv
        """
        log.warning(
            "The function 'upload_df_to_blob' will be deprecated in favour of a more generic version 'upload_to_blob' in the near future.",
        )
        self.create_container(container_name)

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_path,
        )

        try:
            blob_client.upload_blob(
                dataframe.to_csv(index=False, header=True).encode(),
            )
            log.info(f"Dataset uploaded at blob path : {blob_path}.")
        except ResourceExistsError:
            log.warning(
                f"Blob path {blob_path} already contains datas. Now deleting old datas tu upload the new ones.",
            )
            blob_client.delete_blob()
            blob_client.upload_blob(
                dataframe.to_csv(index=False, header=True).encode(),
            )
            log.info(f"New dataset uploaded at blob path : {blob_path}.")

    def download_from_blob(self, container_name: str, blob_path: str) -> StringIO:
        """Download a file a the given `blob_path` location and renders it as a StringIO buffer.

        ```bash
        Storage_Account : workspaceperso5448820782
            │
            ├── Container : project-mlops-mk-5448820782
            │   ├── blob : train
            │   │           ├── x_train.csv
            │   │           └── y_train.csv
            │   └── blob : test
        ```

        ```python
        from azure_helper.utils.blob_storage_interface import BlobStorageInterface

        blob_storage_interface = BlobStorageInterface(
            storage_acct_name="workspaceperso5448820782",
            storage_acct_key="XXXXX-XXXX-XXXXX-XXXX",
            )

        df_buffer = blob_storage_interface.download_from_blob(
            container_name="project-mlops-mk-5448820782",
            blob_path="train/x_train.csv",
        )
        # now convert to csvt to read it.
        dataframe = pd.read_csv(df_buffer)
        ```

        Args:
            container_name (str): The name of the container.
            blob_path (str): The path to the `csv` file.

        Returns:
            StringIO: the file as a StringIO buffer.
        """

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_path,
        )
        stream = blob_client.download_blob()
        buffer = StringIO(stream.content_as_text())
        log.info(f"Download from {container_name} ended successfully.")
        return buffer

    def download_blob_to_df(self, container_name: str, blob_path: str) -> pd.DataFrame:
        """Download a `csv` file a the given `blob_path` location and renders it as a pandas datatrame.

        ```bash
        Storage_Account : workspaceperso5448820782
            │
            ├── Container : project-mlops-mk-5448820782
            │   ├── blob : train
            │   │           ├── x_train.csv
            │   │           └── y_train.csv
            │   └── blob : test
        ```

        ```python
        from azure_helper.utils.blob_storage_interface import BlobStorageInterface

        blob_storage_interface = BlobStorageInterface(
            storage_acct_name="workspaceperso5448820782",
            storage_acct_key="XXXXX-XXXX-XXXXX-XXXX",
            )

        df = blob_storage_interface.download_blob_to_df(
            container_name="project-mlops-mk-5448820782",
            blob_path="train/x_train.csv",
        )
        ```

        Args:
            container_name (str): The name of the container.
            blob_path (str): The path to the `csv` file.

        Returns:
            pd.DataFrame: the `csv` file as a dataframe.
        """
        log.warning(
            "The function 'download_blob_to_df' will be deprecated in favour of a more generic version 'download_from_blob' in the near future.",
        )

        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_path,
        )
        stream = blob_client.download_blob()
        buffer = StringIO(stream.content_as_text())
        dataframe = pd.read_csv(buffer)
        log.info(f"Download from {container_name} ended successfully.")
        return dataframe
