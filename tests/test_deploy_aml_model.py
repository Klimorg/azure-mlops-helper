# from pathlib import Path
# from unittest.mock import Mock

# from azure_helper.steps.deploy_aml_model import DeploymentSettings, DeployModel

# test_module = "azure_helper.steps.deploy_aml_model"


# class TestDeployAMLModel:
#     def test_get_inference_config(
#         self,
#         mocker,
#     ):

#         # We are not testing Azure ML SDK functionality in a unit test
#         # Rather that the correct calls are made

#         mock_inference_config = mocker.patch(f"{test_module}.InferenceConfig")
#         mock_inference_config_obj = Mock()
#         mock_config = Mock()
#         mock_inference_config_obj.return_value = mock_config

#         mock_env = mocker.patch(f"{test_module}.Environment")

#         mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")

#         workspace_name = "test_workspace"
#         resource_group = "test_rg"
#         subscription_id = "test_sub_id"

#         spn_credentials = {
#             "tenant_id": "test_tenant_id",
#             "service_principal_id": "test_spn_id",
#             "service_principal_password": "test_spn_passwd",
#         }

#         aml_interface = mock_aml_inteface(
#             spn_credentials,
#             subscription_id,
#             workspace_name,
#             resource_group,
#         )

#         settings = DeploymentSettings(
#             deployment_service_name="test_deployment_service_name",
#             cpu_cores=1,
#             gpu_cores=0,
#             memory_gb=1,
#             enable_app_insights=True,
#         )

#         deployment = DeployModel(
#             aml_interface=aml_interface,
#             aml_env_name="test_aml_env_name",
#             model_name="test_model_name",
#             script_config_path=Path("test_data/test_score.py"),
#             deployment_settings=settings,
#         )

#         mock_config = deployment.get_inference_config()

#         mock_env.get.assert_called_once()
#         mock_inference_config.assert_called_once()

#     def test_deploy_aciservice(
#         self,
#         mocker,
#     ):
#         mock_get_inference_config = mocker.patch(
#             f"{test_module}.DeployModel.get_inference_config",
#         )
#         mock_config = Mock()
#         mock_get_inference_config.return_value = mock_config

#         mock_AciWebservice = mocker.patch(f"{test_module}.AciWebservice")
#         mock_Model = mocker.patch(f"{test_module}.Model")
#         mock_service = Mock()
#         mock_service.scoring_uri = "https://foo.bar/"
#         mock_Model.deploy.return_value = mock_service

#         mock_env = mocker.patch(f"{test_module}.Environment")

#         mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")

#         workspace_name = "test_workspace"
#         resource_group = "test_rg"
#         subscription_id = "test_sub_id"

#         spn_credentials = {
#             "tenant_id": "test_tenant_id",
#             "service_principal_id": "test_spn_id",
#             "service_principal_password": "test_spn_passwd",
#         }

#         aml_interface = mock_aml_inteface(
#             spn_credentials,
#             subscription_id,
#             workspace_name,
#             resource_group,
#         )

#         settings = DeploymentSettings(
#             deployment_service_name="test_deployment_service_name",
#             cpu_cores=1,
#             gpu_cores=0,
#             memory_gb=1,
#             enable_app_insights=True,
#         )

#         deployment = DeployModel(
#             aml_interface=aml_interface,
#             aml_env_name="test_aml_env_name",
#             model_name="test_model_name",
#             script_config_path=Path("test_data/test_score.py"),
#             deployment_settings=settings,
#         )

#         deployment.deploy_aciservice()

#         mock_get_inference_config.assert_called_once()
#         mock_AciWebservice.deploy_configuration.assert_called_once_with(
#             cpu_cores=1,
#             memory_gb=1,
#             enable_app_insights=True,
#         )

#         mock_Model.deploy.assert_called_once()

#         mock_service.wait_for_deployment.assert_called_once()

#     def test_deploy_aksservice(self, mocker, caplog):

#         aks_cluster_name = "test_aks_cluster_name"

#         mock_ComputeTarget = mocker.patch(f"{test_module}.ComputeTarget")

#         mock_get_inference_config = mocker.patch(
#             f"{test_module}.DeployModel.get_inference_config",
#         )
#         mock_config = Mock()
#         mock_get_inference_config.return_value = mock_config

#         mock_AksWebservice = mocker.patch(f"{test_module}.AksWebservice")

#         mock_Model = mocker.patch(f"{test_module}.Model")
#         mock_service = Mock()
#         mock_service.scoring_uri = "https://foo.bar/"
#         mock_Model.deploy.return_value = mock_service

#         mock_env = mocker.patch(f"{test_module}.Environment")

#         mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")

#         workspace_name = "test_workspace"
#         resource_group = "test_rg"
#         subscription_id = "test_sub_id"

#         spn_credentials = {
#             "tenant_id": "test_tenant_id",
#             "service_principal_id": "test_spn_id",
#             "service_principal_password": "test_spn_passwd",
#         }

#         aml_interface = mock_aml_inteface(
#             spn_credentials,
#             subscription_id,
#             workspace_name,
#             resource_group,
#         )

#         settings = DeploymentSettings(
#             deployment_service_name="test_deployment_service_name",
#             cpu_cores=1,
#             gpu_cores=0,
#             memory_gb=1,
#             enable_app_insights=True,
#         )

#         deployment = DeployModel(
#             aml_interface=aml_interface,
#             aml_env_name="test_aml_env_name",
#             model_name="test_model_name",
#             script_config_path=Path("test_data/test_score.py"),
#             deployment_settings=settings,
#         )

#         deployment.deploy_aksservice(aks_cluster_name=aks_cluster_name)

#         mock_get_inference_config.assert_called_once()
#         mock_AksWebservice.deploy_configuration.assert_called_once_with(
#             cpu_cores=1,
#             memory_gb=1,
#             enable_app_insights=True,
#         )

#         mock_Model.deploy.assert_called_once()

#         mock_service.wait_for_deployment.assert_called_once()

#     # def test_deploy_aksservice_no_cluster(
#     #     self,
#     #     mocker,
#     #     caplog,
#     # ):
#     #     aks_cluster_name = "test_aks_cluster_name"

#     #     mock_compute_target = mocker.patch(f"{test_module}.ComputeTarget")

#     #     mock_compute = Mock()
#     #     mock_compute_target.create.return_value = mock_compute

#     #     mock_aks_compute = mocker.patch(f"{test_module}.AksCompute")

#     #     mock_get_inference_config = mocker.patch(
#     #         f"{test_module}.DeployModel.get_inference_config",
#     #     )
#     #     mock_config = Mock()
#     #     mock_get_inference_config.return_value = mock_config

#     #     mock_aks_webservice = mocker.patch(f"{test_module}.AksWebservice")

#     #     mock_Model = mocker.patch(f"{test_module}.Model")
#     #     mock_service = Mock()
#     #     mock_service.scoring_uri = "https://foo.bar/"
#     #     mock_Model.deploy.return_value = mock_service

#     #     mock_env = mocker.patch(f"{test_module}.Environment")

#     #     mock_aml_inteface = mocker.patch(f"{test_module}.AMLInterface")

#     #     workspace_name = "test_workspace"
#     #     resource_group = "test_rg"
#     #     subscription_id = "test_sub_id"

#     #     spn_credentials = {
#     #         "tenant_id": "test_tenant_id",
#     #         "service_principal_id": "test_spn_id",
#     #         "service_principal_password": "test_spn_passwd",
#     #     }

#     #     aml_interface = mock_aml_inteface(
#     #         spn_credentials,
#     #         subscription_id,
#     #         workspace_name,
#     #         resource_group,
#     #     )

#     #     settings = DeploymentSettings(
#     #         deployment_service_name="test_deployment_service_name",
#     #         cpu_cores=1,
#     #         gpu_cores=0,
#     #         memory_gb=1,
#     #         enable_app_insights=True,
#     #     )

#     #     deployment = DeployModel(
#     #         aml_interface=aml_interface,
#     #         aml_env_name="test_aml_env_name",
#     #         model_name="test_model_name",
#     #         script_config_path=Path("test_data/test_score.py"),
#     #         deployment_settings=settings,
#     #     )

#     #     mock_compute_target.side_effect = ComputeTargetException

#     #     deployment.deploy_aksservice(
#     #         aks_cluster_name=aks_cluster_name,
#     #     )

#     #     assert (
#     #         f"k8s cluster {aks_cluster_name} was not found in workspace test_workspace. Now provisioning one."
#     #         in caplog.records[0].message
#     #     )

#     def test_update_service(self, mocker):

#         mock_get_inference_config = mocker.patch(
#             f"{test_module}.DeployModel.get_inference_config",
#         )
#         mock_config = Mock()
#         mock_get_inference_config.return_value = mock_config

#         mock_aml_interface = mocker.patch(f"{test_module}.AMLInterface")

#         mock_Webservice = mocker.patch(f"{test_module}.Webservice")
#         mock_Webservice_obj = Mock()
#         mock_Webservice.return_value = mock_Webservice_obj

#         workspace_name = "test_workspace"
#         resource_group = "test_rg"
#         subscription_id = "test_sub_id"

#         spn_credentials = {
#             "tenant_id": "test_tenant_id",
#             "service_principal_id": "test_spn_id",
#             "service_principal_password": "test_spn_passwd",
#         }

#         aml_interface = mock_aml_interface(
#             spn_credentials,
#             subscription_id,
#             workspace_name,
#             resource_group,
#         )
#         aml_interface.workspace.models.get.return_value = "test_model_name"

#         settings = DeploymentSettings(
#             deployment_service_name="test_deployment_service_name",
#             cpu_cores=1,
#             gpu_cores=0,
#             memory_gb=1,
#             enable_app_insights=True,
#         )

#         deployment = DeployModel(
#             aml_interface=aml_interface,
#             aml_env_name="test_aml_env_name",
#             model_name="test_model_name",
#             script_config_path=Path("test_data/test_score.py"),
#             deployment_settings=settings,
#         )

#         deployment.update_service()
#         mock_get_inference_config.assert_called_once()
#         mock_Webservice_obj.update.assert_called_once_with(
#             models=["test_model_name"],
#             inference_config=mock_config,
#         )


# # @patch("src.my_custom_package.deploy_aml_model.Webservice")
# # @patch("src.my_custom_package.deploy_aml_model.get_inference_config")
# # def test_update_service(mock_get_inference_config, mock_Webservice):
# #     mock_aml_interface = Mock()
# #     mock_get_inference_config.return_value = "test_inference_config"
# #     mock_aml_interface.workspace.models.get.return_value = "test_model_name"
# #     mock_service = Mock()
# #     mock_Webservice.return_value = mock_service

# #     update_service(mock_aml_interface)
# #     # mock_get_inference_config is tested independently above
# #     mock_get_inference_config.assert_called_once()
# #     mock_service.update.assert_called_once_with(
# #         models=["test_model_name"],
# #         inference_config="test_inference_config",
# #     )
