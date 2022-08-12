from unittest.mock import Mock

import pandas as pd
from azure.core.exceptions import ResourceExistsError
from pytest import fixture

from azure_helper.utils.blob_storage_interface import BlobStorageInterface

test_module = "azure_helper.utils.blob_storage_interface"


@fixture
def blob_storage_resources(mocker):
    blob_service_client_obj = Mock()

    mock_blob_service_client = mocker.patch(f"{test_module}.BlobServiceClient")
    mock_blob_service_client.from_connection_string.return_value = (
        blob_service_client_obj
    )

    blob_storage_interface = BlobStorageInterface(
        "test_storage_acct_name",
        "test_storage_acct_key",
    )

    return mock_blob_service_client, blob_service_client_obj, blob_storage_interface


class TestBlobStorageInterface:
    def test_init(self, blob_storage_resources):

        mock_blob_service_client, _, _ = blob_storage_resources

        mock_blob_service_client.from_connection_string.assert_called_once_with(
            "DefaultEndpointsProtocol=https;"
            + "AccountName=test_storage_acct_name;"
            + "AccountKey=test_storage_acct_key;"
            + "EndpointSuffix=core.windows.net",
        )

    def test_create_container(self, blob_storage_resources, caplog):

        _, blob_service_client_obj, blob_storage_interface = blob_storage_resources

        blob_service_client_obj.create_container.side_effect = [
            None,
            ResourceExistsError,
        ]
        blob_storage_interface.create_container("test_container_name")

        blob_service_client_obj.create_container.assert_called_with(
            "test_container_name",
        )

        # Upon second call to BlobStorageInterface.create_container,
        # ResourceExistsError is raised from
        # BlobStorageInterface.blob_service_client.create_container
        # Second call checks that no error is raised from
        # BlobStorageInterface.create_container
        # with pytest.raises(ResourceExistsError) as err:
        blob_storage_interface.create_container("test_container_name")
        assert len(caplog.records) == 2
        assert (
            "Blob storage container test_container_name already exists"
            in caplog.records[1].message
        )

    def test_upload_df_to_blob(self, blob_storage_resources, caplog):

        _, blob_service_client_obj, blob_storage_interface = blob_storage_resources

        mock_blob_client = Mock()
        mock_blob_client.upload_blob.side_effect = [
            None,
            ResourceExistsError,
            None,
        ]
        blob_service_client_obj.get_blob_client.return_value = mock_blob_client

        test_df = pd.DataFrame([{"a": 1, "b": 2}, {"a": 3, "b": 4}])

        blob_storage_interface.upload_df_to_blob(
            test_df,
            "test_container_name",
            "test_remote_path",
        )

        assert (
            "Dataset uploaded at blob path : test_remote_path."
            in caplog.records[1].message
        )

        blob_service_client_obj.get_blob_client.assert_called_with(
            container="test_container_name",
            blob="test_remote_path",
        )
        mock_blob_client.upload_blob.assert_called()
        args, _ = mock_blob_client.upload_blob.call_args_list[0]
        upload_arg = args[0]
        # The file uploaded is uploaded as bytes
        assert isinstance(upload_arg, bytes)

        # First time upload_df_to_blob is called, there is no
        # ResourceExistsError so the blob is not deleted
        mock_blob_client.delete_blob.assert_not_called()

        # 2nd call to upload_df_to_blob
        blob_storage_interface.upload_df_to_blob(
            test_df,
            "test_container_name",
            "test_remote_path",
        )
        assert len(caplog.records) == 5
        assert (
            "Blob path test_remote_path already contains datas. Now deleting old datas tu upload the new ones."
            in caplog.records[3].message
        )
        # Second time upload_df_to_blob is called, there is a
        # ResourceExistsError raised so the blob is deleted first
        mock_blob_client.delete_blob.assert_called_once()
        mock_blob_client.upload_blob.assert_called()

    def test_download_blob_to_df(self, blob_storage_resources, caplog):

        _, blob_service_client_obj, blob_storage_interface = blob_storage_resources

        mock_blob_client = Mock()
        mock_stream = Mock()
        test_csv_str = "a,b\n1,2\n3,4"

        blob_service_client_obj.get_blob_client.return_value = mock_blob_client
        mock_blob_client.download_blob.return_value = mock_stream
        mock_stream.content_as_text.return_value = test_csv_str

        output_df = blob_storage_interface.download_blob_to_df(
            "test_container_name",
            "test_remote_path",
        )

        assert isinstance(output_df, pd.DataFrame)
        assert "a" in output_df.columns
        assert output_df.loc[1, "b"] == 4

        blob_service_client_obj.get_blob_client.assert_called_once_with(
            container="test_container_name",
            blob="test_remote_path",
        )
        mock_blob_client.download_blob.assert_called_once()
        mock_stream.content_as_text.assert_called_once()

        assert len(caplog.records) == 1
        assert (
            "Download from test_container_name ended successfully."
            in caplog.records[0].message
        )
