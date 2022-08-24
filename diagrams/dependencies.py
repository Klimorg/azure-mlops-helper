from diagrams import Cluster, Diagram, Edge
from diagrams.azure.ml import MachineLearningServiceWorkspaces as Workspace
from diagrams.onprem.container import Docker
from diagrams.programming.language import Python

with Diagram(
    "Azure MLOps helper dependency diagram",
    show=False,
    outformat=["svg", "png"],
) as dac:
    dac.dot.renderer = "cairo"

    data = Python("BlobStorageInterface")
    env = Python("AMLEnvironment")
    exp = Python("AMLExperiment")
    deploy = Python("DeployModel")

    interface = Python("AMLInterface")

    with Cluster("Workspace"):
        ws = Workspace("Workspace")

        with Cluster("Assets"):
            ws_env = Workspace("Environments")
            ws_data = Workspace("Datastores")
            ws_exp = Workspace("Experiments")
            ws_model = Workspace("Models")

    env >> Edge(label="create") >> interface
    interface >> Edge(label="register environment") >> ws_env

    data >> Edge(label="create") >> interface
    interface >> Edge(label="register datastore") >> ws_data

    exp << Edge(label="fetch workspace") << interface
    exp << Edge(label="fetch env") << ws_env
    exp >> Edge(label="submit_run") >> ws_exp
    exp >> Edge(label="register_model") >> ws_model
    # interface >> Edge(xlabel="connexion") >> ws
    # interface >> Edge(xlabel="get compute") >> ws

    # deploy << Edge(xlabel="fetch workspace") << interface
