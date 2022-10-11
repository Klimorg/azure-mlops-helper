from pathlib import Path
from typing import List

from azure.ai.ml import command
from azure.ai.ml.entities import Environment

from azure_helper.interfaces.aml_interface import AMLInterface
from azure_helper.logger import get_logger

# from azureml.core import Experiment, ScriptRunConfig
# from azureml.core.runconfig import DockerConfiguration, RunConfiguration
# from azureml.pipeline.core import Pipeline
# from azureml.pipeline.steps import PythonScriptStep


log = get_logger()


class AMLExperiment:
    def __init__(
        self,
        aml_interface: AMLInterface,
        aml_compute_name: str,
        aml_compute_instance: str,
        env_name: str,
        experiment_name: str,
        training_script_path: str,
        min_node: int = 1,
        max_node: int = 2,
        clean_after_run: bool = True,
    ) -> None:
        """Instantiate the creation of an AzureML Experiment needed to train a model.

        Args:
            aml_interface (AMLInterface): The aml_interface needed to register the experiment in the workspace.
            aml_compute_name (str): The name of the compute instance used.
            aml_compute_instance (str): The size (as in `vm_size`) of the compute instance used.
            min_node (int, optional): The minimum number of nodes to use on the compute instance. Defaults to 1.
            max_node (int, optional): The maximum number of nodes to use on the compute instance. Defaults to 2.
            env_name (str): The name of the training environment.
            experiment_name (str): The name of the experiment.
            training_script_path (str): The path to the training loop script.
            clean_after_run (bool, optional): Whether or not you want to delete the compute instance after training. Defaults to True.
        """

        self.aml_interface = aml_interface
        self.aml_compute_name = aml_compute_name
        self.aml_compute_instance = aml_compute_instance
        self.env_name = env_name
        self.experiment_name = experiment_name
        self.clean_after_run = clean_after_run
        self.training_script_path = training_script_path

        # self.compute_target = aml_interface.get_compute_target(
        #     aml_compute_name,
        #     aml_compute_instance,
        #     min_node,
        #     max_node,
        # )

    def generate_run(self):
        """Generate the run configuration of the experiment.

        By definition, the run configuration is the combination of the training environment and the compute instance.

        Returns:
            RunConfiguration: The run configuration of the experiment.
        """

        # run_config = RunConfiguration()
        # docker_config = DockerConfiguration(use_docker=True)
        # run_config.docker = docker_config

        # aml_run_env = Environment.get(
        #     self.interface.workspace,
        #     self.env_name,
        # )

        # run_config.environment = aml_run_env

        # run_config.target = self.compute_target
        src_dir = str(Path.cwd())

        job = command(
            code=src_dir,
            command=self.training_script_path,
            environment=f"{self.env_name}@latest",
            compute=self.aml_compute_name,
            display_name=self.experiment_name,
        )

        return job

    # def submit_run(self, job):
    #     """Submit your training loop and create an experiment.

    #     This experiment is defined by the use of the `ScriptRunConfig` class.
    #     This means that you have to provide the path to a script defining your training loop, defined by the parameters
    #     `source_directory` and `script` of the `ScriptRunConfig` class, `script` being the path of your training loop
    #     relative to `source_directory`.

    #     For example purpose, a training loop example is provided [TrainingLoopExample][azure_helper.steps.train] is
    #     provided, as well as an abstract class if you want to use this training loop structure, but you're not forced to.
    #     """

    #     returned_job = self.aml_interface.create_or_update(job)
    #     aml_url = returned_job.studio_url
    #     print("Monitor your job at", aml_url)
