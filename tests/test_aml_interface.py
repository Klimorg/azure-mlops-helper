from unittest.mock import Mock

from azureml.exceptions import ComputeTargetException
from pytest import fixture

from azure_helper.utils.aml_interface import AMLInterface

test_module = "azure_helper.utils.aml_interface"


@fixture
def aml_interface(mocker):
    mocker_spn = mocker.patch(
        f"{test_module}.ServicePrincipalAuthentication",
    )
    mock_workspace = mocker.patch(
        f"{test_module}.Workspace",
        return_value="test_workspace",
    )
    spn_credentials = {
        "tenant_id": "test_tenant_id",
        "service_principal_id": "test_spn_id",
        "service_principal_password": "test_spn_password",
    }
    return AMLInterface(
        spn_credentials=spn_credentials,
        subscription_id="test_subscription_id",
        workspace_name="test_workspace_name",
        resource_group="test_resource_group",
    )


class TestAMLInterface:
    def test_register_datastore(self, mocker, aml_interface):

        mock_datastore = mocker.patch(
            f"{test_module}.Datastore",
        )

        aml_interface.register_datastore(
            "test_datastore_name",
            "test_blob_container",
            "test_storage_acct_name",
            "test_storage_acct_key",
        )

        mock_datastore.register_azure_blob_container.assert_called_once_with(
            workspace="test_workspace",
            datastore_name="test_datastore_name",
            container_name="test_blob_container",
            account_name="test_storage_acct_name",
            account_key="test_storage_acct_key",
        )

    def register_aml_environment(self, aml_interface):
        mock_environment = Mock()

        aml_interface.register_aml_environment(mock_environment)

        mock_environment.register.assert_called_once_with("test_workspace")

    def test_get_compute_target(self, mocker, aml_interface):
        mock_compute_target = mocker.patch(
            f"{test_module}.ComputeTarget",
        )
        mock_AmlCompute = mocker.patch(
            f"{test_module}.AmlCompute",
        )

        mock_compute_target_obj = Mock()
        mock_compute_target.create.return_value = mock_compute_target_obj

        # First call to mock_compute_target returns 'test_compute_target'
        compute_target = aml_interface.get_compute_target(
            "test_compute_name",
            "STANDARD_D2_V2",
        )
        #  {'currentNodeCount': 1, 'targetNodeCount': 1, 'nodeStateCounts': {'preparingNodeCount': 0, 'runningNodeCount': 0, 'idleNodeCount': 1, 'unusableNodeCount': 0, 'leavingNodeCount': 0, 'preemptedNodeCount': 0}, 'allocationState': 'Steady', 'allocationStateTransitionTime': '2022-08-11T13:48:24.409000+00:00', 'errors': None, 'creationTime': '2022-08-11T13:46:01.432646+00:00', 'modifiedTime': '2022-08-11T13:46:08.602275+00:00', 'provisioningState': 'Succeeded', 'provisioningStateTransitionTime': None, 'scaleSettings': {'minNodeCount': 1, 'maxNodeCount': 2, 'nodeIdleTimeBeforeScaleDown': 'PT1800S'}, 'vmPriority': 'Dedicated', 'vmSize': 'STANDARD_D2_V2'}
        # assert mock_compute_target_obj.status.serialized().vmSize == "STANDARD_D2_V2"

        mock_compute_target.create.assert_not_called()

        mock_compute_target.side_effect = ComputeTargetException(
            "Compute Target Not Found",
        )
        mock_compute = Mock()
        # Compute target exists, create not called
        mock_compute_target.create.return_value = mock_compute

        # Second call to mock_compute_target raises ComputeTargetException
        # Suggesting the compute target needs to be created
        output_2 = aml_interface.get_compute_target(
            "test_compute_name",
            "STANDARD_D2_V2",
        )

        assert output_2 == mock_compute

        mock_AmlCompute.provisioning_configuration.assert_called_once_with(
            vm_size="STANDARD_D2_V2",
            min_nodes=1,
            max_nodes=2,
        )
        mock_compute_target.create.assert_called_once()
        mock_compute.wait_for_completion.assert_called_once()
