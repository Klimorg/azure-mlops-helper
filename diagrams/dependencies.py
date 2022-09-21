from diagrams import Cluster, Diagram, Edge
from diagrams.azure.devops import Pipelines, Repos
from diagrams.azure.ml import MachineLearningServiceWorkspaces as Workspace
from diagrams.onprem.container import Docker
from diagrams.programming.language import Python

with Diagram(
    "Azure MLOps helper dependency diagram",
    show=False,
    outformat=["svg", "png"],
) as dac:
    dac.dot.renderer = "cairo"

    with Cluster("ML Resources Creation"):

        data = Python("BlobStorageInterface")
        interface = Python("AMLInterface")
        env = Python("AMLEnvironment")

    with Cluster("ML Training"):

        exp = Python("AMLExperiment")

    with Cluster("Workspace"):
        ws = Workspace("Workspace")

        with Cluster("Assets"):
            ws_env = Workspace("Environments")
            ws_data = Workspace("Datastores")
            ws_exp = Workspace("Experiments")
            ws_model = Workspace("Models")

    env << interface
    interface >> Edge(label="register environment") >> ws_env

    data << interface
    interface >> Edge(label="register datastore") >> ws_data

    exp << Edge(label="fetch workspace") << interface
    exp << Edge(label="fetch env") << ws_env
    exp >> Edge(label="submit_run") >> ws_exp
    exp >> Edge(label="register_model") >> ws_model

    with Cluster("Repo"):
        Repos("Repo")
        with Cluster("Azure DevOps ML Resources"):
            devops_data = Pipelines("Data Creation")
            devops_env = Pipelines("Environment Creation")
            # devops_exp = Pipelines("Training pipeline")

        with Cluster("Azure DevOps ML Training"):
            # devops_data = Pipelines("Data Creation")
            # devops_env = Pipelines("Environment Creation")
            devops_exp = Pipelines("Training pipeline")

            (
                devops_data
                >> Edge(label="trigger")
                >> devops_env
                >> Edge(label="trigger")
                >> devops_exp
            )

    devops_data >> data
    devops_env >> env
    devops_exp >> exp
