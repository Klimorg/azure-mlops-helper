from pathlib import Path

from azureml.core.environment import Environment
from pydantic import BaseModel

from azure_helper.interfaces.aml_interface import AMLInterface
from azure_helper.logger import get_logger

log = get_logger()


class EnvSpecs(BaseModel):
    """Pydantic class used to specify how to build the environment : with pip, conda or docker.

    Args:
        flavor (str): Which method you chose, either pip, conda of docker.
        spec_file (Path): The path to either the `requirements.txt` files, the `environment.yml` file, or the `Dockerfile`.
    """

    flavor: str
    spec_file: Path


class AMLEnvironment:
    def __init__(self, private_wheel_location: Path, base_image: str) -> None:
        """Instantiate the creation of the AzureML Environment needed for the experiment.

        An AzureML Environment is a Docker Image which encapsulates all the needed requirements for the experiment (ie
        the training of a model) to run, this can be :

        * the version of the OS,
        * the various python libraries needed (ie the `requirements.txt`),
        * the project built as a wheel and added as a private pip package,
        * third-party softwares, etc.

        To create the Docker image of the environment, we use a base image managed by Microsoft. This image can be changed corresponding to the
        need of the experiment.

        The standard image we use is `mcr.microsoft.com/azureml/curated/sklearn-1.0-ubuntu20.04-py38-cpu`.

        The different images managed by Microsoft can be found ine the [Azure Machine Learning base images](https://github.com/Azure/AzureML-Containers).

        The create the Docker image of the environment, we also need the project, built as a pip wheel (by Flit, setuptools, Hatch, etc),
        so we can install it in our environment.

        Args:
            dist_dir (Path): The path where the project built as a wheel is located.
            base_image (str): The base Docker image we use to create the environment.
        """
        self.private_wheel_location = private_wheel_location
        self.base_image = base_image

    def validate_dir(self):
        """Small validation to check if a given path is a valid path in the project.

        Raises:
            FileNotFoundError: The path does not point to a valid directory.
        """
        if self.private_wheel_location.is_dir():
            log.info(f"Looking for wheel file in {self.private_wheel_location}.")
        else:
            raise FileNotFoundError

    def retrieve_whl_filepath(self) -> Path:
        """The project inside you develop your model you want to train need to be build as a pip wheel and added to the training environement.

        Once your project has been build as a pip wheel (by Flit, setuptools, Hatch, etc), given the location of the distribution directory
        (usually `$cwd/dist`), this function looks for a `.whl` file and return its path.

        !!! remark "Remark"

            Usually, there is only one `.whl` file in a `dist` directory. This is an assumption of this function.

        Raises:
            FileNotFoundError: Either the `dist` directory path is not valid, or there is no `.whl` file inside.

        Returns:
            Path: The path of the private wheel package.
        """
        try:
            self.validate_dir()
        except FileNotFoundError:
            log.error(
                f"Couldn't find distribution directory {self.private_wheel_location}",
            )
            raise

        whl_file = sorted(
            Path(file)
            for file in Path(self.private_wheel_location).glob("**/*.whl")
            if file.is_file()
        )
        if len(whl_file) == 0:
            log.error("Couldn't find wheel distribution")
            raise FileNotFoundError

        log.info(f"Found wheel {self.private_wheel_location / Path(whl_file[0])}")

        return self.private_wheel_location / Path(whl_file[0])

    def create_aml_environment(
        self,
        env_name: str,
        env_specs: EnvSpecs,
        aml_interface: AMLInterface,
    ) -> Environment:
        """Create the AzureML Environment once all the requirements have been gathered.

        Args:
            env_name (str): The name of the environment that will be build.
            env_specs (EnvSpecs): The specifications used to create the environement (ie pip, conda, or docker).
            aml_interface (AMLInterface): The AML interface which will be responsible to register the environment in the right workspace.

        Raises:
            ValueError: You have selected something else than "pip", "conda", or "docker" for the `EnvSpecs`.

        Returns:
            Environment: The training environment which will be used.

        !!! remark "Remark"
            The environment returned is just a Dockerfile, it not built as an image and will have to be built during the first training.
            If you want to build it locally, you will have to put `build_locally=True` in `AMLInterface.register_aml_environment`.
        """
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
                f"env_specs flavor {env_specs.flavor} is not a valid one. Only 'pip', 'conda', or 'docker' are valid choices.",
            )
            raise ValueError

        whl_filepath = self.retrieve_whl_filepath()
        private_wheel = env.add_private_pip_wheel(
            workspace=aml_interface.workspace,
            file_path=whl_filepath,
            exist_ok=True,
        )
        env.python.conda_dependencies.add_pip_package(private_wheel)

        env.docker.base_image = self.base_image

        # env.python.user_managed_dependencies = True
        # https://stackoverflow.com/questions/67387249/how-to-use-azureml-core-runconfig-dockerconfiguration-class-in-azureml-core-envi

        return env
