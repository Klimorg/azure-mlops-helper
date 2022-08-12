from typing import Dict

from azureml.core import Datastore, Workspace
from azureml.core.authentication import ServicePrincipalAuthentication
from azureml.core.compute import AmlCompute, ComputeTarget
from azureml.core.environment import Environment
from azureml.exceptions import ComputeTargetException

from azure_helper.logger import get_logger

log = get_logger()


class AMLInterface:
    def __init__(
        self,
        spn_credentials: Dict[str, str],
        subscription_id: str,
        workspace_name: str,
        resource_group: str,
    ):
        """Instantiate an Azure Machine Learning Workspace and its connection to Azure DevOps.

        Parameters
        ----------
        spn_credentials : Dict[str, str]
            Credentials of the Service Principal used to communicate betwee the different resources of the workspace.
            Must contains the TenantID and the ServicePrincipalID.
        subscription_id : str
            The Azure subscription ID containing the workspace.
        workspace_name : str
            The workspace name. The name must be between 2 and 32 characters long.
            The first character of the name must be alphanumeric (letter or number), but the rest of the name may
            contain alphanumerics, hyphens, and underscores. Whitespace is not allowed.
        resource_group : str
            The resource group containing the workspace.
        """
        auth = ServicePrincipalAuthentication(**spn_credentials)
        self.workspace = Workspace(
            workspace_name=workspace_name,
            auth=auth,
            subscription_id=subscription_id,
            resource_group=resource_group,
        )

    def register_datastore(
        self,
        datastore_name: str,
        container_name: str,
        storage_acct_name: str,
        storage_acct_key: str,
    ):
        """Register an Azure Blob Container to the datastore.

        Parameters
        ----------
        datastore_name : str
            The name of the datastore, case insensitive, can only contain alphanumeric characters and -.
        blob_container : str
            The name of the azure blob container.
        storage_acct_name : str
            The storage account name.
        storage_acct_key : str
            Access keys of your storage account, defaults to None.
        """
        Datastore.register_azure_blob_container(
            workspace=self.workspace,
            datastore_name=datastore_name,
            container_name=container_name,
            account_name=storage_acct_name,
            account_key=storage_acct_key,
        )

    def register_aml_environment(self, environment: Environment):
        """Register the environment object in your workspace.

        Parameters
        ----------
        environment : Environment
            A reproducible Python environment for machine learning experiments.
        """
        environment.register(workspace=self.workspace)

    def get_compute_target(self, compute_name: str, vm_size: str = "") -> ComputeTarget:
        """Instantiate a compute instance to train the models.

        Parameters
        ----------
        compute_name : str
            The name of the compute instance.
        vm_size : str, optional
            The size of agent VMs in the the compute instance. More details can be found here: https://aka.ms/azureml-vm-details.
            Note that not all sizes are available in all regions, as detailed in the previous link.
            If not specified, defaults to Standard_NC6. By default ""

        Returns
        -------
        ComputeTarget
            An instantiated compute instance.
        """
        try:
            compute_target = ComputeTarget(
                workspace=self.workspace,
                name=compute_name,
            )
            log.info("Found existing compute target")
            log.info(
                f"Compute target instantiated : {compute_target.status.serialize()}",
            )
        except ComputeTargetException as err:
            log.info(f"No compute target found. Creating a new compute target. {err}")
            compute_config = AmlCompute.provisioning_configuration(
                vm_size=vm_size,
                min_nodes=1,
                max_nodes=2,
            )
            compute_target = ComputeTarget.create(
                self.workspace,
                compute_name,
                compute_config,
            )
            compute_target.wait_for_completion(
                show_output=True,
                timeout_in_minutes=10,
            )
            log.info(
                f"Compute target instantiated : {compute_target.status.serialize()}",
            )
        return compute_target
