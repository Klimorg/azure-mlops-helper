from azure.ai.ml import MLClient
from azure.ai.ml.entities import AmlCompute, AzureBlobDatastore, Environment
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

from azure_helper.logger import get_logger

log = get_logger()


class AMLInterface:
    def __init__(
        self,
        managed_id: str,
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

        It is responsible for :

        * Connect to an existing Storage Account and promote blob inside a specified container into an Azure Machine Learning Datastores.
        * Register Azure Machine Learning Environment created by the [`AMLEnvironment`][azure_helper.steps.create_aml_env] class as Docker Image.
        * Provisioning Compute Instance, either by fetching an existing one or creating a new one.


        Args:
            subscription_id (str): The Azure subscription ID containing the workspace.
            workspace_name (str): The workspace name. The name must be between 2 and 32 characters long.
                The first character of the name must be alphanumeric (letter or number), but the rest of the name may
                contain alphanumerics, hyphens, and underscores. Whitespace is not allowed.
            resource_group (str): The resource group containing the workspace.
        """
        auth = DefaultAzureCredential()
        # auth = ManagedIdentityCredential()
        self.workspace = MLClient(
            credential=auth,
            workspace_name=workspace_name,
            subscription_id=subscription_id,
            resource_group_name=resource_group,
        )

    def register_datastore(
        self,
        datastore_name: str,
        container_name: str,
        storage_acct_name: str,
        description: str,
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
            description="small description,
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
            description (str): Small description of the datastore.
        """
        store = AzureBlobDatastore(
            name=datastore_name,
            container_name=container_name,
            account_name=storage_acct_name,
            description=description,
        )

        self.workspace.create_or_update(store)

    def register_aml_environment(
        self,
        environment: Environment,
    ):
        """Register the environment object in your workspace.

        An environement created by the [`AMLEnvironment`][azure_helper.steps.create_aml_env] class encapsulate in a Docker image
        everything which is needed to make to project work. See its documentation for further explainations.

        Args:
            environment (Environment): A reproducible Python environment for machine learning experiments.
        """

        self.workspace.environments.create_or_update(environment)

    def submit_experiment(self, job):
        """Register the environment object in your workspace.

        An environement created by the [`AMLEnvironment`][azure_helper.steps.create_aml_env] class encapsulate in a Docker image
        everything which is needed to make to project work. See its documentation for further explainations.

        Args:
            environment (Environment): A reproducible Python environment for machine learning experiments.
        """

        returned_job = self.workspace.create_or_update(job)
        aml_url = returned_job.studio_url
        log.info(f"Monitor your job at {aml_url}")

    def get_compute_target(
        self,
        compute_name: str,
        vm_size: str = "",
        min_node: int = 1,
        max_node: int = 2,
    ) -> AmlCompute:
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
            ComputeInstance: An instantiated compute instance.
        """
        compute_name = compute_name
        cluster_basic = AmlCompute(
            name=compute_name,
            size=vm_size,
            min_instances=min_node,
            max_instances=max_node,
        )

        self.workspace.begin_create_or_update(cluster_basic)

        log.info(
            f"Compute target instantiated : {self.workspace.compute.get(compute_name)}",
        )
        return cluster_basic
