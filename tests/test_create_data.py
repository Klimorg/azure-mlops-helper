import pandas as pd
from pytest import fixture
from sklearn.datasets import make_classification

from azure_helper.steps.create_data import CreateData


@fixture
def train_data():
    x_arr, y_arr = make_classification(
        n_samples=5000,
        n_features=10,
        n_classes=2,
        random_state=1,
    )
    col_names = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
    ]
    x_df = pd.DataFrame(x_arr, columns=col_names)
    y_df = pd.DataFrame({"Target": y_arr})
    # Training set n=3500
    x_train = x_df.iloc[:3500]
    y_train = y_df.iloc[:3500]

    return x_train, y_train


@fixture
def test_data():
    x_arr, y_arr = make_classification(
        n_samples=5000,
        n_features=10,
        n_classes=2,
        random_state=1,
    )
    col_names = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
    ]
    x_df = pd.DataFrame(x_arr, columns=col_names)
    y_df = pd.DataFrame({"Target": y_arr})

    # Testing set n=750
    x_test = x_df.iloc[3500:4250]
    y_test = y_df.iloc[3500:4250]

    return x_test, y_test


@fixture
def val_data():
    x_arr, y_arr = make_classification(
        n_samples=5000,
        n_features=10,
        n_classes=2,
        random_state=1,
    )
    col_names = [
        "A",
        "B",
        "C",
        "D",
        "E",
        "F",
        "G",
        "H",
        "I",
        "J",
    ]
    x_df = pd.DataFrame(x_arr, columns=col_names)
    y_df = pd.DataFrame({"Target": y_arr})

    # Validation set n=750
    x_val = x_df.iloc[4250:]
    y_val = y_df.iloc[4250:]

    return x_val, y_val


class TestCreateClassificationData:
    def test_init(self, train_data, test_data, val_data):

        x_train, y_train = train_data
        x_test, y_test = test_data
        x_valid, y_valid = val_data

        assert isinstance(x_train, pd.DataFrame)
        assert isinstance(x_test, pd.DataFrame)
        assert isinstance(x_valid, pd.DataFrame)
        assert isinstance(y_train, pd.DataFrame)
        assert isinstance(y_test, pd.DataFrame)
        assert isinstance(y_valid, pd.DataFrame)

        # Train data is 3500 rows
        # X data is 10 columns, y data is 1 column
        assert len(x_train) == 3500
        assert len(x_train.columns) == 10
        assert len(y_train) == 3500
        assert len(y_train.columns) == 1

        # Test data is 750 rows
        assert len(x_test) == 750
        assert len(x_test.columns) == 10
        assert len(y_test) == 750
        assert len(y_test.columns) == 1

        # Validation data is 750 rows
        assert len(x_valid) == 750
        assert len(x_valid.columns) == 10
        assert len(y_valid) == 750
        assert len(y_valid.columns) == 1

    def test_upload_training_data(self, mocker, train_data):

        x_train, y_train = train_data
        mock_blob_storage_interface = mocker.patch(
            "azure_helper.steps.create_data.BlobStorageInterface",
        )

        data_creator = CreateData(
            project_name="test_project",
            train_datastore="train",
            test_datastore="test",
        )

        data_creator.upload_training_data(mock_blob_storage_interface, x_train, y_train)
        assert mock_blob_storage_interface.upload_df_to_blob.call_count == 2

    def test_upload_test_data(self, mocker, test_data):
        x_test, y_test = test_data

        mock_blob_storage_interface = mocker.patch(
            "azure_helper.steps.create_data.BlobStorageInterface",
        )
        data_creator = CreateData(
            project_name="test_project",
            train_datastore="train",
            test_datastore="test",
        )
        data_creator.upload_test_data(mock_blob_storage_interface, x_test, y_test)

        assert mock_blob_storage_interface.upload_df_to_blob.call_count == 2

    def test_upload_validation_data(self, mocker, val_data):
        x_valid, y_valid = val_data

        mock_blob_storage_interface = mocker.patch(
            "azure_helper.steps.create_data.BlobStorageInterface",
        )
        data_creator = CreateData(
            project_name="test_project",
            train_datastore="train",
            test_datastore="test",
        )
        data_creator.upload_validation_data(
            mock_blob_storage_interface,
            x_valid,
            y_valid,
        )

        assert mock_blob_storage_interface.upload_df_to_blob.call_count == 2
