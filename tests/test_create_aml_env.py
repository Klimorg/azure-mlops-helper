from pathlib import Path
from unittest.mock import Mock

import pytest
from azureml.core.conda_dependencies import CondaDependencies

from azure_helper.logger import get_logger
from azure_helper.steps.create_aml_env import AMLEnvironment, EnvSpecs

log = get_logger()
test_module = "azure_helper.steps.create_aml_env"

test_whl_dir = Path(__file__).parents[1] / Path("dist")


# def test_get_dist_dir(caplog, mocker):

#     mock_get_dist_dir = mocker.patch(
#         f"{test_module}.get_dist_dir",
#     )
#     mock_get_dist_dir.side_effect = [test_whl_dir, FileNotFoundError]

#     dist_dir = mock_get_dist_dir()

#     assert isinstance(dist_dir, Path)
#     assert dist_dir.stem == "dist"

#     with pytest.raises(FileNotFoundError):
#         dist_dir = mock_get_dist_dir()

#         assert len(caplog) == 1
#         assert (
#             f"Couldn't find distribution directory {test_whl_dir}"
#             in caplog.records[1].message
#         )


class TestRetrieveWhlFilepath:
    def test_validate_dir(self, mocker, tmp_path, caplog):
        dist_dir = tmp_path / Path("test")
        dist_dir.mkdir()

        aml_env = AMLEnvironment(dist_dir=dist_dir)

        aml_env.validate_dir()

        assert len(caplog.records) == 1
        assert f"Looking for wheel file in {dist_dir}." in caplog.records[0].message

        mock_dir = mocker.patch(f"{test_module}.Path.is_dir")
        mock_dir.side_effect = [False]
        with pytest.raises(FileNotFoundError):
            aml_env.validate_dir()

    def test_retrieve_whl_filepath_fails_no_dist_dir(self, mocker, tmp_path, caplog):

        dist_dir = tmp_path / Path("test")

        mock_dir = mocker.patch(f"{test_module}.Path.is_dir")
        mock_dir.side_effect = [False]
        aml_env = AMLEnvironment(dist_dir=dist_dir)

        with pytest.raises(FileNotFoundError):
            aml_env.retrieve_whl_filepath()

        assert len(caplog.records) == 1
        assert (
            f"Couldn't find distribution directory {dist_dir}"
            in caplog.records[0].message
        )

    def test_retrieve_whl_filepath_fails_no_file(self, tmp_path, caplog):

        file = "azure_helper-0.1-py3.tar.gz"
        whl_filepath = tmp_path / Path(file)
        whl_filepath.touch()

        aml_env = AMLEnvironment(dist_dir=tmp_path)
        with pytest.raises(FileNotFoundError):
            wheel = aml_env.retrieve_whl_filepath()

        assert len(caplog.records) == 2
        assert "Couldn't find wheel distribution" in caplog.records[1].message

    def test_retrieve_whl_filepath(self, tmp_path, caplog):

        file = "azure_helper-0.1-py3.whl"
        whl_filepath = tmp_path / Path(file)
        whl_filepath.touch()

        aml_env = AMLEnvironment(dist_dir=tmp_path)

        filepath = aml_env.retrieve_whl_filepath()

        assert isinstance(filepath, Path)
        assert filepath.suffix == ".whl"
        assert filepath.stem == "azure_helper-0.1-py3"

        assert len(caplog.records) == 2
        assert f"Looking for wheel file in {tmp_path}." in caplog.records[0].message

    def test_create_aml_environment_with_pip(self, mocker, tmp_path):

        # Initiate the class
        env = AMLEnvironment(dist_dir=tmp_path)

        # Mock the Environment class that is called inside AMLEnv
        mock_env = mocker.patch(f"{test_module}.Environment")

        # Mock the AMLInterface class that is called inside AMLEnv
        mock_aml_interface = mocker.patch(f"{test_module}.AMLInterface")

        # Create some temp files and dirs to do the tests
        file = "azure_helper-0.1-py3.whl"
        whl_filepath = tmp_path / Path(file)
        whl_filepath.touch()

        spec_dir = tmp_path / Path("specs")
        spec_dir.mkdir()

        spec_file = spec_dir / Path("requirements.txt")
        spec_file.write_text("numpy==1.18.2")
        spec_file.touch()

        # Define the type of env we want to test, ie pip environment type
        env_specs = EnvSpecs(flavor="pip", spec_file=spec_file)

        aml_env = env.create_aml_environment(
            env_name="test_env_name",
            env_specs=env_specs,
            aml_interface=mock_aml_interface,
        )

        mock_env.from_pip_requirements.assert_called_once_with(
            name="test_env_name",
            file_path=str(spec_file),
        )

        aml_env.add_private_pip_wheel.assert_called_once_with(
            workspace=mock_aml_interface.workspace,
            file_path=whl_filepath,
            exist_ok=True,
        )

    def test_create_aml_environment_with_docker(self, mocker, tmp_path):

        # Initiate the class
        env = AMLEnvironment(dist_dir=tmp_path)

        # Mock the Environment class that is called inside AMLEnv
        mock_env = mocker.patch(f"{test_module}.Environment")
        mock_env_obj = Mock()
        mock_env.return_value = mock_env_obj

        # Mock the AMLInterface class that is called inside AMLEnv
        mock_aml_interface = mocker.patch(f"{test_module}.AMLInterface")

        # Create some temp files and dirs to do the tests
        file = "azure_helper-0.1-py3.whl"
        whl_filepath = tmp_path / Path(file)
        whl_filepath.touch()

        spec_dir = tmp_path / Path("specs")
        spec_dir.mkdir()

        spec_file = spec_dir / Path("Dockerfile")
        spec_file.write_text("FROM ubuntu:20.04")
        spec_file.touch()

        # Define the type of env we want to test, ie pip environment type
        env_specs = EnvSpecs(flavor="docker", spec_file=spec_file)

        aml_env = env.create_aml_environment(
            env_name="test_env_name",
            env_specs=env_specs,
            aml_interface=mock_aml_interface,
        )

        mock_env.from_dockerfile.assert_called_once_with(
            name="test_env_name",
            dockerfile=str(spec_file),
        )

        aml_env.add_private_pip_wheel.assert_called_once_with(
            workspace=mock_aml_interface.workspace,
            file_path=whl_filepath,
            exist_ok=True,
        )

        log.warning(f"{mock_env_obj.python.conda_dependencies.pip_packages}")
        # pkg_list = [pkg for pkg in mock_env_obj.python.conda_dependencies.pip_packages]
        # assert "numpy==1.18.2" in pkg_list

        # assert aml_env.docker.base_image == "python:3.8.13"

    def test_create_aml_environment_with_error(self, mocker, tmp_path, caplog):

        # Initiate the class
        env = AMLEnvironment(dist_dir=tmp_path)

        # Mock the Environment class that is called inside AMLEnv
        mock_env = mocker.patch(f"{test_module}.Environment")

        # Mock the AMLInterface class that is called inside AMLEnv
        mock_aml_interface = mocker.patch(f"{test_module}.AMLInterface")

        # Create some temp files and dirs to do the tests
        file = "azure_helper-0.1-py3.whl"
        whl_filepath = tmp_path / Path(file)
        whl_filepath.touch()

        spec_dir = tmp_path / Path("specs")
        spec_dir.mkdir()

        spec_file = spec_dir / Path("Dockerfile")
        spec_file.write_text("FROM ubuntu:20.04")
        spec_file.touch()

        # Define the type of env we want to test, ie pip environment type
        env_specs = EnvSpecs(flavor="foobar", spec_file=spec_file)

        with pytest.raises(ValueError):

            aml_env = env.create_aml_environment(
                env_name="test_env_name",
                env_specs=env_specs,
                aml_interface=mock_aml_interface,
            )

        assert len(caplog.records) == 1
        assert (
            "env_specs flavor foobar is not a valid one. Only 'pip', 'conda', or 'docker' are valide choices."
            in caplog.records[0].message
        )
