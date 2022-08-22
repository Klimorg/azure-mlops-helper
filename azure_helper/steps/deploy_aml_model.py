import os

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
    """_summary_

    Args:
        BaseModel (_type_): _description_
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
        """_summary_

        Args:
            aml_interface (AMLInterface): _description_
            aml_env_name (str): _description_
            model_name (str): _description_
            deployment_settings (DeploymentSettings): _description_
        """

        self.aml_interface = aml_interface
        self.workspace = aml_interface.workspace

        self.aml_env_name = aml_env_name
        self.model_name = model_name
        self.deployment_settings = deployment_settings

    def get_inference_config(
        self,
    ) -> InferenceConfig:
        """_summary_

        Returns:
            _type_: _description_
        """

        aml_env = Environment.get(
            workspace=self.workspace,
            name=self.aml_env_name,
        )
        scoring_script_path = os.path.join(__here__, "score.py")
        return InferenceConfig(
            entry_script=scoring_script_path,
            environment=aml_env,
        )

    def deploy_aciservice(
        self,
        *args,
        **kwargs,
    ) -> Webservice:
        """_summary_"""

        inference_config = self.get_inference_config()

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
        aks_cluster_name: str,
        *args,
        **kwargs,
    ) -> Webservice:
        """_summary_

        Args:
            aks_cluster_name (str): _description_
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

        inference_config = self.get_inference_config()

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
    ):
        """_summary_"""
        inference_config = self.get_inference_config()
        service = Webservice(
            name=self.deployment_settings.deployment_service_name,
            workspace=self.workspace,
        )
        model = self.workspace.models.get(self.model_name)
        service.update(models=[model], inference_config=inference_config)
        log.info(service.state)
        log.info(service.scoring_uri)


def main():
    # Retrieve vars from env
    workspace_name = os.environ["AML_WORKSPACE_NAME"]
    resource_group = os.environ["RESOURCE_GROUP"]
    subscription_id = os.environ["SUBSCRIPTION_ID"]

    spn_credentials = {
        "tenant_id": os.environ["TENANT_ID"],
        "service_principal_id": os.environ["SPN_ID"],
        "service_principal_password": os.environ["SPN_PASSWORD"],
    }

    aml_interface = AMLInterface(
        spn_credentials,
        subscription_id,
        workspace_name,
        resource_group,
    )
    webservices = aml_interface.workspace.webservices.keys()
    if DEPLOYMENT_SERVICE_NAME not in webservices:
        deploy_service(aml_interface)
    else:
        update_service(aml_interface)
