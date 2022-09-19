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
        """Instantiate the connection to an Azure Machine Learning Workspace.

        This class is the principal interface with the other ones. It uses a Service Principle **with Password Authentication** connection to interact with Azure
        Machine Learning. The Service Principle credentials needed can be encapsulated in the following Pydantic class.

        ```python
        from pydantic import BaseSettings, Field

        class SpnCredentials(BaseSettings):
            tenant_id: str = Field(env="TENANT_ID")
            service_principal_id: str = Field(env="SPN_ID")
            service_principal_password: str = Field(env="SPN_PASSWORD")
        ```

        !!! info "Information"

            To create a Service Principle with Password Authentication, you can do it using the azure-cli with the following shell command.

            `az ad sp create-for-rbac --name <spn-name>`

            It is important to note down the app id and password from the creation of this service principal! You’ll also need the tenant ID listed here.


        !!! attention "Attention"

            The service principal also needs to have a contributor role in the IAM management of the ressource group.

        It is responsible for :

        * Connect to an existing Storage Account and promote blob inside a specified container into an Azure Machine Learning Datastores.
        * Register Azure Machine Learning Environment created by the [`AMLEnvironment`][azure_helper.steps.create_aml_env] class as Docker Image.
        * Provisioning Compute Instance, either by fetching an existing one or creating a new one.


        Args:
            spn_credentials (Dict[str, str]): Credentials of the Service Principal used to communicate between the different resources of the workspace.
                Must contains the TenantID and the ServicePrincipalID.
            subscription_id (str): The Azure subscription ID containing the workspace.
            workspace_name (str): The workspace name. The name must be between 2 and 32 characters long.
                The first character of the name must be alphanumeric (letter or number), but the rest of the name may
                contain alphanumerics, hyphens, and underscores. Whitespace is not allowed.
            resource_group (str): The resource group containing the workspace.
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
        """Register an Azure Blob Container as an AZML datastore.

        ie if you have an architecture like the following one.

        ```bash
        Storage_Account : workspaceperso5448820782
            │
            ├── Container : project-mlops-mk-5448820782
            │   ├── blob : train
            │   └── blob : test
        ```

        Then


        ```py
        aml_interface.register_datastore(
            datastore_name="project_name",
            container_name="project-mlops-mk-5448820782",
            storage_acct_name="workspaceperso5448820782",
            storage_acct_key="storage_acct_key",
            )
        ```

        Will register the Blob container `project-mlops-mk-5448820782` as an AZML datastore under the name `project_name`.


        !!! attention "Attention"

            We are talking here about **datastores**, not **datasets**, which are special data assets of a datastore.

            Eg, in the following architecture.

            ```bash
            Storage_Account : workspaceperso5448820782
                │
                ├── Container : project-mlops-mk-5448820782
                │   ├── blob : train
                │   │           ├── x_train.csv
                │   │           └── y_train.csv
                │   └── blob : test
            ```

            `x_train.csv` and `y_train.csv` can be registered as datasets.

        Args:
            datastore_name (str): The name of the AZML datastore, case insensitive, can only contain alphanumeric characters and -.
            container_name (str): The name of the azure blob container.
            storage_acct_name (str): The storage account name.
            storage_acct_key (str): Access keys of your storage account, defaults to None.
        """
        Datastore.register_azure_blob_container(
            workspace=self.workspace,
            datastore_name=datastore_name,
            container_name=container_name,
            account_name=storage_acct_name,
            account_key=storage_acct_key,
        )

    def register_aml_environment(
        self,
        environment: Environment,
        build_locally: bool = False,
    ):
        """Register the environment object in your workspace.

        An environement created by the [`AMLEnvironment`][azure_helper.steps.create_aml_env] class encapsulate in a Docker image
        everything which is needed to make to project work. See its documentation for further explainations.

        Args:
            environment (Environment): A reproducible Python environment for machine learning experiments.
            build_locally (bool, optional): Whether you want to build locally your environment as a Docker image and push the image
                to workspace ACR directly. This is recommended when users are iterating on the dockerfile since local build
                can utilize cached layers. Defaults to False.
        """
        environment.register(workspace=self.workspace)
        if build_locally:
            environment.build_local(
                self.workspace,
                useDocker=True,
                pushImageToWorkspaceAcr=True,
            )

    def get_compute_target(
        self,
        compute_name: str,
        vm_size: str = "",
        min_node: int = 1,
        max_node: int = 2,
    ) -> ComputeTarget:
        """Instantiate a compute instance to train the models.

        If no Compute Instance with the specified parameters is found in the workspace, a new one will be created.

        Args:
            compute_name (str): The name of the compute instance.
            vm_size (str): The size of agent VMs in the the compute instance.
                More details can be found [here](https://aka.ms/azureml-vm-details).
                Note that not all sizes are available in all regions, as detailed in the previous link.
                If not specified, (ie `vm_size = ""`) defaults to `Standard_NC6`.
            min_node (int, optional): The minimum number of nodes to use on the cluster. Defaults to 1.
            max_node (int, optional): The maximum number of nodes to use on the cluster. Defaults to 2.


        Returns:
            ComputeTarget: An instantiated compute instance.
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
            log.warning(
                f"No compute target found. Creating a new compute target. {err}",
            )
            compute_config = AmlCompute.provisioning_configuration(
                vm_size=vm_size,
                min_nodes=min_node,
                max_nodes=max_node,
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
