import os
from pathlib import Path

from azureml.core.compute import AksCompute
from azureml.core.environment import Environment
from azureml.core.model import InferenceConfig, Model
from azureml.core.webservice import AciWebservice, AksWebservice, Webservice
from azureml.exceptions import ComputeTargetException
from pydantic import BaseModel

from azure_helper.logger import get_logger
from azure_helper.utils.aml_interface import AMLInterface

__here__ = os.path.dirname(__file__)

log = get_logger()


class DeploymentSettings(BaseModel):
    """Basic settings needed for the deployment, whether it is with ACI or AKS.

    Args:
        deployment_service_name (str): the name of the service you want to deploy or update.
        cpu_cores (int): The number of cpu cores needed. Defaults to 1.
        gpu_cores (int): The number of gpu cores needed. Defaults to 0.
        memory_gb (int): The memory in gb needed. Defaults to 1.
        enable_app_insights (bool): Enable app insights monitoring. Defaults to True.
    """

    deployment_service_name: str
    cpu_cores: int = 1
    gpu_cores: int = 0
    memory_gb: int = 1
    enable_app_insights: bool = True


class DeployModel:
    def __init__(
        self,
        aml_interface: AMLInterface,
        aml_env_name: str,
        model_name: str,
        deployment_settings: DeploymentSettings,
    ) -> None:
        """Instantiate the deployment of the model.

        Args:
            aml_interface (AMLInterface):  The AMLInterface which will be responsible to deploy the model.
            aml_env_name (str): The name of the AMLEnvironment you will use to deploy the model. It is not necessarily
                the same used to train the model.
            model_name (str): The name of the model you deploy.
            deployment_settings (DeploymentSettings): the basic settings of the deployment.
        """

        self.aml_interface = aml_interface
        self.workspace = aml_interface.workspace

        self.aml_env_name = aml_env_name
        self.model_name = model_name
        self.deployment_settings = deployment_settings

    def get_inference_config(
        self,
        script_config_path: Path,
    ) -> InferenceConfig:
        """Fetch the inference script config needed to interact the endpoint deployed.

        Args:
            script_config_path (Path): The location of the script.

        Returns:
            InferenceConfig: The instantiated inference config.
        """

        aml_env = Environment.get(
            workspace=self.workspace,
            name=self.aml_env_name,
        )
        # scoring_script_path = os.path.join(__here__, "score.py")
        scoring_script_path = str(script_config_path)
        return InferenceConfig(
            entry_script=scoring_script_path,
            environment=aml_env,
        )

    def deploy_aciservice(
        self,
        script_config_path: Path,
        *args,
        **kwargs,
    ):
        """Deploy an ACI service to serve the model.

        Args:
            script_config_path (Path): The location of the script for the inference config.
        """
        inference_config = self.get_inference_config(script_config_path)

        aci_deployment = AciWebservice.deploy_configuration(
            *args,
            **kwargs,
            cpu_cores=self.deployment_settings.cpu_cores,
            memory_gb=self.deployment_settings.memory_gb,
            enable_app_insights=self.deployment_settings.enable_app_insights,
        )

        model = self.workspace.models.get(self.model_name)

        service = Model.deploy(
            self.workspace,
            self.deployment_settings.deployment_service_name,
            [model],
            inference_config,
            aci_deployment,
        )

        service.wait_for_deployment(show_output=True)
        log.info(service.state)
        log.info(service.scoring_uri)

    def deploy_aksservice(
        self,
        script_config_path: Path,
        aks_cluster_name: str,
        *args,
        **kwargs,
    ):
        """Deploy an AKS service to serve the model.


        Args:
            script_config_path (Path): The location of the script for the inference config.
            aks_cluster_name (str): The name of the k8s cluster on which you want to deploy. Contrary to an ACI deployment,
                you need a pre-existing k8s cluster in your workspace to use AKS deployment.
        """

        try:
            aks_target = AksCompute(self.workspace, name=aks_cluster_name)
            log.info(
                f"k8s cluster {aks_cluster_name} found in workspace {self.workspace}",
            )
        except ComputeTargetException:
            log.error(
                f"k8s cluster {aks_cluster_name} was not found in workspace {self.workspace}",
            )
            raise

        inference_config = self.get_inference_config(script_config_path)

        aks_deployment = AksWebservice.deploy_configuration(
            *args,
            **kwargs,
            cpu_cores=self.deployment_settings.cpu_cores,
            memory_gb=self.deployment_settings.memory_gb,
            enable_app_insights=self.deployment_settings.enable_app_insights,
        )

        model = self.workspace.models.get(self.model_name)

        service = Model.deploy(
            self.workspace,
            self.deployment_settings.deployment_service_name,
            [model],
            inference_config,
            aks_deployment,
            aks_target,
        )

        service.wait_for_deployment(show_output=True)
        log.info(service.state)
        log.info(service.scoring_uri)

    def update_service(
        self,
        script_config_path: Path,
    ):
        """Update an already existing service, ACI or AKS.

        Args:
            script_config_path (Path): The location of the script for the inference config.
        """
        inference_config = self.get_inference_config(script_config_path)
        service = Webservice(
            name=self.deployment_settings.deployment_service_name,
            workspace=self.workspace,
        )
        model = self.workspace.models.get(self.model_name)
        service.update(models=[model], inference_config=inference_config)
        log.info(service.state)
        log.info(service.scoring_uri)


# def main():
#     # Retrieve vars from env
#     workspace_name = os.environ["AML_WORKSPACE_NAME"]
#     resource_group = os.environ["RESOURCE_GROUP"]
#     subscription_id = os.environ["SUBSCRIPTION_ID"]

#     spn_credentials = {
#         "tenant_id": os.environ["TENANT_ID"],
#         "service_principal_id": os.environ["SPN_ID"],
#         "service_principal_password": os.environ["SPN_PASSWORD"],
#     }

#     aml_interface = AMLInterface(
#         spn_credentials,
#         subscription_id,
#         workspace_name,
#         resource_group,
#     )
#     webservices = aml_interface.workspace.webservices.keys()
#     if DEPLOYMENT_SERVICE_NAME not in webservices:
#         deploy_service(aml_interface)
#     else:
#         update_service(aml_interface)
