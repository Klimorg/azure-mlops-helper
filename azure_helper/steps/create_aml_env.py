from pathlib import Path

from azureml.core.environment import Environment
from pydantic import BaseModel

from azure_helper.logger import get_logger
from azure_helper.utils.aml_interface import AMLInterface

log = get_logger()


class EnvSpecs(BaseModel):
    flavor: str
    spec_file: Path


class AMLEnvironment:
    def __init__(self, dist_dir: Path) -> None:
        self.dist_dir = dist_dir

    def validate_dir(self):
        if self.dist_dir.is_dir():
            log.info(f"Looking for wheel file in {self.dist_dir}.")
        else:
            raise FileNotFoundError

    def retrieve_whl_filepath(self):
        try:
            self.validate_dir()
        except FileNotFoundError:
            log.error(f"Couldn't find distribution directory {self.dist_dir}")
            raise

        whl_file = sorted(
            Path(file)
            for file in Path(self.dist_dir).glob("**/*.whl")
            if file.is_file()
        )
        if len(whl_file) == 0:
            log.error("Couldn't find wheel distribution")
            raise FileNotFoundError

        log.info(f"Found wheel {self.dist_dir / Path(whl_file[0])}")

        return self.dist_dir / Path(whl_file[0])

    def create_aml_environment(
        self,
        env_name: str,
        env_specs: EnvSpecs,
        aml_interface: AMLInterface,
    ) -> Environment:
        if env_specs.flavor == "pip":
            env = Environment.from_pip_requirements(
                name=env_name,
                file_path=str(env_specs.spec_file),
            )
        elif env_specs.flavor == "conda":
            env = Environment.from_conda_specification(
                name=env_name,
                file_path=str(env_specs.spec_file),
            )
        elif env_specs.flavor == "docker":
            env = Environment.from_dockerfile(
                name=env_name,
                dockerfile=str(env_specs.spec_file),
            )
        else:
            log.error(
                f"env_specs flavor {env_specs.flavor} is not a valid one. Only 'pip', 'conda', or 'docker' are valide choices.",
            )
            raise ValueError

        whl_filepath = self.retrieve_whl_filepath()
        private_wheel = env.add_private_pip_wheel(
            workspace=aml_interface.workspace,
            file_path=whl_filepath,
            exist_ok=True,
        )
        env.python.conda_dependencies.add_pip_package(private_wheel)

        # conda_dep.add_pip_package(whl_url)
        # https://docs.microsoft.com/en-us/azure/machine-learning/how-to-train-with-custom-image#set-up-a-training-experiment
        env.docker.base_image = (
            "mcr.microsoft.com/azureml/curated/sklearn-1.0-ubuntu20.04-py38-cpu:28"
        )
        # env.python.user_managed_dependencies = True

        # https://stackoverflow.com/questions/67387249/how-to-use-azureml-core-runconfig-dockerconfiguration-class-in-azureml-core-envi

        return env
