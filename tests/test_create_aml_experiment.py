from unittest.mock import Mock

from azureml.core import ScriptRunConfig
from azureml.pipeline.core import Pipeline

from azure_helper.steps.create_aml_experiment import AMLExperiment

test_module = "azure_helper.steps.create_aml_experiment"


class TestAMLExperiment:
    def test_submit_run(self, mocker, caplog):
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
        mock_aml_inteface_obj = Mock()
        mock_compute_target = Mock()
        mock_aml_inteface.return_value = mock_aml_inteface_obj
        mock_aml_inteface_obj.get_compute_target.return_value = mock_compute_target

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
            training_script_path="azure_helper/steps/train.py",
            min_node=1,
            max_node=2,
            clean_after_run=True,
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

        mock_compute_target.delete.assert_called_once()

        assert len(caplog.records) == 3

    def test_submit_run_no_clean_after_run(self, mocker, caplog):
        # We are not testing Azure ML SDK functionality in a unit test
        # Rather that the correct calls are made

        mock_env = mocker.patch(f"{test_module}.Environment")

        # we mock the Experiment class
        mock_experiment = mocker.patch(f"{test_module}.Experiment")
        # this class is instantiated in AMLExperiment and must return an object when submitted
        # so we mock both : the instantiated class and the returned object when submitted
        mock_experiment_obj = Mock()
        mock_run = Mock()
        mock_experiment.return_value = mock_experiment_obj
        mock_experiment_obj.submit.return_value = mock_run

        mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")
        # this class is instantiated in AMLExperiment and must return an object when submitted
        # so we mock both : the instantiated class and the returned object when submitted
        mock_aml_inteface_obj = Mock()
        mock_compute_target = Mock()
        mock_aml_inteface.return_value = mock_aml_inteface_obj
        mock_aml_inteface_obj.get_compute_target.return_value = mock_compute_target

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
            training_script_path="azure_helper/steps/train.py",
            min_node=1,
            max_node=2,
            clean_after_run=False,
        )

        aml_exp.submit_run()

        mock_env.get.assert_called_once()

        mock_experiment_obj.submit.assert_called_once()

        aml_interface.get_compute_target.assert_called_once_with(
            "test_compute_name",
            "STANDARD_D2_V2",
            1,
            2,
        )

        _, kwargs = mock_experiment_obj.submit.call_args_list[0]
        exp_config = kwargs["config"]
        assert isinstance(exp_config, ScriptRunConfig)
        assert exp_config.script == "azure_helper/steps/train.py"

        mock_run.wait_for_completion.assert_called_once_with(show_output=True)
        mock_run.get_metrics.assert_called_once()

        aml_interface.get_compute_target.assert_called_once()

        mock_compute_target.delete.assert_not_called()

        assert len(caplog.records) == 2

    def test_generate_run_config(self, mocker):
        # We are not testing Azure ML SDK functionality in a unit test
        # Rather that the correct calls are made

        mock_env = mocker.patch(f"{test_module}.Environment")
        mock_env_obj = Mock()
        mock_env.get.return_value = mock_env_obj

        mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")
        # this class is instantiated in AMLExperiment and must return an object when submitted
        # so we mock both : the instantiated class and the returned object when submitted

        workspace_name = "test_workspace"
        resource_group = "test_rg"
        subscription_id = "test_sub_id"

        spn_credentials = {
            "tenant_id": "test_tenant_id",
            "service_principal_id": "test_spn_id",
            "service_principal_password": "test_spn_passwd",
        }

        mock_aml_inteface_obj = mock_aml_inteface(
            spn_credentials,
            subscription_id,
            workspace_name,
            resource_group,
        )

        aml_exp = AMLExperiment(
            aml_interface=mock_aml_inteface_obj,
            aml_compute_name="test_compute_name",
            aml_compute_instance="STANDARD_D2_V2",
            env_name="test_env_name",
            experiment_name="test_exp_name",
            training_script_path="azure_helper/steps/train.py",
            min_node=1,
            max_node=2,
            clean_after_run=False,
        )

        run_config = aml_exp.generate_run_config()

        assert run_config.environment == mock_env_obj
        assert run_config.target == "local"

    def test_submit_ipeline(self, mocker, caplog):
        # We are not testing Azure ML SDK functionality in a unit test
        # Rather that the correct calls are made
        mock_env = mocker.patch(f"{test_module}.Environment")

        mock_pipeline = mocker.patch(f"{test_module}.Pipeline")

        # we mock the Experiment class
        mock_experiment = mocker.patch(f"{test_module}.Experiment")
        # this class is instantiate in AMLExperiment and must return an object when submitted
        # so we mock both : the instantiated class and the returned object when submitted
        mock_experiment_obj = Mock()
        mock_run = Mock()
        mock_experiment.return_value = mock_experiment_obj
        mock_experiment_obj.submit.return_value = mock_run

        mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")
        mock_aml_inteface_obj = Mock()
        mock_compute_target = Mock()
        mock_aml_inteface.return_value = mock_aml_inteface_obj
        mock_aml_inteface_obj.get_compute_target.return_value = mock_compute_target

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
            training_script_path="azure_helper/steps/train.py",
            min_node=1,
            max_node=2,
            clean_after_run=True,
        )

        step1 = Mock()
        step2 = Mock()

        aml_exp.submit_pipeline(steps=[step1, step2])

        mock_experiment_obj.submit.assert_called_once()

        aml_interface.get_compute_target.assert_called_once()

        mock_run.wait_for_completion.assert_called_once_with(show_output=True)

        mock_compute_target.delete.assert_called_once()

        assert len(caplog.records) == 3
