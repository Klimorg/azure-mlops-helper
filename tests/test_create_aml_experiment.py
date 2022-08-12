from unittest.mock import Mock

from azureml.core import ScriptRunConfig

from azure_helper.steps.create_aml_experiment import AMLExperiment

test_module = "azure_helper.steps.create_aml_experiment"


class TestAMLExperiment:
    def test_submit_run(self, mocker):
        # We are not testing Azure ML SDK functionality in a unit test
        # Rather that the correct calls are made

        mock_env = mocker.patch(f"{test_module}.Environment")

        # we mock the Experiment class
        mock_experiment = mocker.patch(f"{test_module}.Experiment")
        # this class is instantiate in AMLExperiment and must return an object when submitted
        # so we mock both : the instantiated class and the returned object when submitted
        mock_experiment_obj = Mock()
        mock_run = Mock()
        mock_experiment.return_value = mock_experiment_obj
        mock_experiment_obj.submit.return_value = mock_run

        mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")

        workspace_name = "test_workspace"
        resource_group = "test_rg"
        subscription_id = "test_sub_id"

        spn_credentials = {
            "tenant_id": "test_tenant_id",
            "service_principal_id": "test_spn_id",
            "service_principal_password": "test_spn_passwd",
        }

        aml_interface = mock_aml_inteface(
            spn_credentials,
            subscription_id,
            workspace_name,
            resource_group,
        )

        aml_exp = AMLExperiment(
            aml_interface=aml_interface,
            aml_compute_name="test_compute_name",
            aml_compute_instance="STANDARD_D2_V2",
            env_name="test_env_name",
            experiment_name="test_exp_name",
        )

        aml_exp.submit_run()

        mock_env.get.assert_called_once()

        mock_experiment_obj.submit.assert_called_once()

        aml_interface.get_compute_target.assert_called_once()

        _, kwargs = mock_experiment_obj.submit.call_args_list[0]
        exp_config = kwargs["config"]
        assert isinstance(exp_config, ScriptRunConfig)
        assert exp_config.script == "azure_helper/steps/train.py"

        mock_run.wait_for_completion.assert_called_once_with(show_output=True)
        mock_run.get_metrics.assert_called_once()
