import os
from pathlib import Path
from typing import List

from azureml.core import Environment, Experiment, ScriptRunConfig
from azureml.core.runconfig import DockerConfiguration, RunConfiguration
from azureml.pipeline.core import Pipeline
from azureml.pipeline.steps import PythonScriptStep

from azure_helper.logger import get_logger
from azure_helper.utils.aml_interface import AMLInterface

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
        clean_after_run: bool = True,
    ) -> None:
        """_summary_

        Args:
            aml_interface (AMLInterface): _description_
            aml_compute_name (str): _description_
            aml_compute_instance (str): _description_
            env_name (str): _description_
            experiment_name (str): _description_
            training_script_path (str): _description_
            clean_after_run (bool, optional): _description_. Defaults to True.
        """

        self.interface = aml_interface
        self.aml_compute_name = aml_compute_name
        self.aml_compute_instance = aml_compute_instance
        self.env_name = env_name
        self.experiment_name = experiment_name
        self.clean_after_run = clean_after_run
        self.training_script_path = training_script_path

    def generate_run_config(self) -> RunConfiguration:

        run_config = RunConfiguration()
        docker_config = DockerConfiguration(use_docker=True)
        run_config.docker = docker_config

        aml_run_env = Environment.get(
            self.interface.workspace,
            self.env_name,
        )

        run_config.environment = aml_run_env

        compute_target = self.interface.get_compute_target(
            self.aml_compute_name,
            self.aml_compute_instance,
        )
        run_config.target = compute_target

        return run_config

    def submit_pipeline(self, steps: List[PythonScriptStep]):
        """_summary_

        Args:
            steps (List[PythonScriptStep]): _description_

        https://github.com/Azure/MachineLearningNotebooks/blob/master/how-to-use-azureml/machine-learning-pipelines/intro-to-pipelines/aml-pipelines-getting-started.ipynb

        This should be a registered AZML Pipeline with the followings steps :

        * Download raw datas from one datastore
        * Transform those datas in "gold" datas and store them in another datastore
        * Use these gold datas to train a model
        * Evaluate that model
        * Save and version that model

        """
        experiment = Experiment(self.interface.workspace, self.experiment_name)
        # src_dir = __here__
        # src_dir = str(Path.cwd())

        compute_target = self.interface.get_compute_target(
            self.aml_compute_name,
            self.aml_compute_instance,
        )

        pipeline = Pipeline(workspace=self.interface.workspace, steps=steps)

        log.info("Submitting Run")
        run = experiment.submit(config=pipeline)
        run.wait_for_completion(show_output=True)
        log.info("Run completed.")

        if self.clean_after_run:
            log.info("Deleting compute instance.")
            compute_target.delete()

    def submit_run(self):
        """_summary_"""

        experiment = Experiment(self.interface.workspace, self.experiment_name)
        # src_dir = __here__
        src_dir = str(Path.cwd())

        docker_config = DockerConfiguration(use_docker=True)
        script = ScriptRunConfig(
            source_directory=src_dir,
            script=self.training_script_path,
            docker_runtime_config=docker_config,
        )

        compute_target = self.interface.get_compute_target(
            self.aml_compute_name,
            self.aml_compute_instance,
        )

        script.run_config.target = compute_target

        aml_run_env = Environment.get(
            self.interface.workspace,
            self.env_name,
        )
        script.run_config.environment = aml_run_env

        log.info("Submitting Run")
        run = experiment.submit(config=script)
        run.wait_for_completion(show_output=True)
        log.info(f"Run completed : {run.get_metrics()}")

        if self.clean_after_run:
            log.info("Deleting compute instance.")
            compute_target.delete()
