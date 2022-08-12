import os
from pathlib import Path

from azureml.core import Environment, Experiment, ScriptRunConfig
from azureml.core.runconfig import DockerConfiguration

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
        clean_after_run: bool = True,
    ) -> None:
        self.interface = aml_interface
        self.aml_compute_name = aml_compute_name
        self.aml_compute_instance = aml_compute_instance
        self.env_name = env_name
        self.experiment_name = experiment_name
        self.clean_after_run = clean_after_run

    def submit_run(self):

        experiment = Experiment(self.interface.workspace, self.experiment_name)
        # src_dir = __here__
        src_dir = str(Path.cwd())

        docker_config = DockerConfiguration(use_docker=True)
        run_config = ScriptRunConfig(
            source_directory=src_dir,
            script="azure_helper/steps/train.py",
            docker_runtime_config=docker_config,
        )

        compute_target = self.interface.get_compute_target(
            self.aml_compute_name,
            self.aml_compute_instance,
        )

        run_config.run_config.target = compute_target

        aml_run_env = Environment.get(
            self.interface.workspace,
            self.env_name,
        )
        run_config.run_config.environment = aml_run_env

        log.info("Submitting Run")
        run = experiment.submit(config=run_config)
        run.wait_for_completion(show_output=True)
        log.info(f"Run completed : {run.get_metrics()}")

        if self.clean_after_run:
            log.info("Deleting compute instance.")
            compute_target.delete()
