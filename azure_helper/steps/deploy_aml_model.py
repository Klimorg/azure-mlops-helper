import os

from azureml.core.environment import Environment
from azureml.core.model import InferenceConfig, Model
from azureml.core.webservice import AciWebservice, Webservice

from azure_helper.utils.aml_interface import AMLInterface
from azure_helper.logger import get_logger
from pydantic import BaseModel

__here__ = os.path.dirname(__file__)

log = get_logger()


class DeploymentSettings(BaseModel):
    deployment_service_name: str
    cpu_cores: int = 1
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
        self.aml_interface = aml_interface
        self.aml_env_name = aml_env_name
        self.model_name = model_name
        self.deployment_settings = deployment_settings

    def get_inference_config(
        self,
    ):

        aml_env = Environment.get(
            workspace=self.aml_interface.workspace,
            name=self.aml_env_name,
        )
        scoring_script_path = os.path.join(__here__, "score.py")
        inference_config = InferenceConfig(
            entry_script=scoring_script_path,
            environment=aml_env,
        )
        return inference_config

    def deploy_aciservice(
        self,
    ):
        inference_config = self.get_inference_config()
        aci_deployment = AciWebservice.deploy_configuration(
            cpu_cores=self.deployment_settings.cpu_cores,
            memory_gb=self.deployment_settings.memory_gb,
            enable_app_insights=self.deployment_settings.enable_app_insights,
        )
        model = self.aml_interface.workspace.models.get(self.model_name)
        service = Model.deploy(
            self.aml_interface.workspace,
            self.deployment_settings.deployment_service_name,
            [model],
            inference_config,
            aci_deployment,
        )
        service.wait_for_deployment(show_output=True)
        log.info(service.scoring_uri)

    def deploy_aksservice(self):
        pass

    def update_service(
        self,
    ):
        inference_config = self.get_inference_config()
        service = Webservice(
            name=self.deployment_settings.deployment_service_name,
            workspace=self.aml_interface.workspace,
        )
        model = self.aml_interface.workspace.models.get(self.model_name)
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
