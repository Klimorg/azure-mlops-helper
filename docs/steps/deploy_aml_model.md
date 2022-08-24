# The Model Deployment

## ::: azure_helper.steps.deploy_aml_model
    options:
      show_root_heading: true
      show_source: true
      members_order: source


## Deploy to AKS

* [Web service authentication](https://docs.microsoft.com/en-us/azure/machine-learning/v1/how-to-deploy-azure-kubernetes-service?tabs=python#web-service-authentication)

When deploying to Azure Kubernetes Service, **key-based authentication is enabled by default**. You can also enable token-based authentication. Token-based authentication requires clients to use an Azure Active Directory account to request an authentication token, which is used to make requests to the deployed service.

### Limitations

* **Using a service principal with AKS is not supported by Azure Machine Learning**. The AKS cluster must use a system-assigned managed identity instead.


### Tutorial

[Prepare an application for Azure Kubernetes Service (AKS)](https://docs.microsoft.com/en-us/azure/aks/tutorial-kubernetes-prepare-app)

#### Create a Kubernetes cluster

```shell
az aks create \
    --resource-group myResourceGroup \
    --name myAKSCluster \
    --node-count 2 \
    --generate-ssh-keys \
    --attach-acr <acrName>
```

#### Install kubectl

```shell
az aks install-cli
```

#### Connect to cluster using kubectl


```shell
az aks get-credentials --resource-group myResourceGroup --name myAKSCluster
```

#### Update the manifest file

In these tutorials, an Azure Container Registry (ACR) instance stores the container image for the sample application. To deploy the application, you must update the image name in the Kubernetes manifest file to include the ACR login server name.

#### Deploy the application

To deploy your application, use the kubectl apply command.

```shell
kubectl apply -f manifest.yaml
```
