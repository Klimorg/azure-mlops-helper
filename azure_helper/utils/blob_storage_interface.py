from io import StringIO

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

from azure_helper.logger import get_logger

log = get_logger()


class BlobStorageInterface:
    def __init__(self, storage_acct_name: str, storage_acct_key: str):
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
        """_summary_

        Args:
            container_name (str): _description_
        """
        try:
            self.blob_service_client.create_container(container_name)
            log.info(f"Creating blob storage container {container_name}.")
        except ResourceExistsError:
            log.warning(f"Blob storage container {container_name} already exists.")
            pass

    def upload_df_to_blob(
        self,
        dataframe: pd.DataFrame,
        container_name: str,
        blob_path: str,
    ):
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

    def download_blob_to_df(self, container_name: str, blob_path: str):
        blob_client = self.blob_service_client.get_blob_client(
            container=container_name,
            blob=blob_path,
        )
        stream = blob_client.download_blob()
        buffer = StringIO(stream.content_as_text())
        dataframe = pd.read_csv(buffer)
        log.info(f"Download from {container_name} ended successfully.")
        return dataframe
