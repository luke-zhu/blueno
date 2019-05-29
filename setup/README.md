This directory contains scripts for setting up a Kubernetes cluster.

The scripts are not customizable, they are here for people who want
to try out the project quickly. Nevertheless, if your requirements change in the future, you can
manually delete and recreate a new Kubernetes cluster with the same Postgres and NFS data.

[//]: # (TODO: Describe how to recreate clusters.)

_At the moment, only Mac and Linux are supported._ 

## Creating a Cluster
Run one of the setup scripts of your choice. For
example, `python3 gke.py`


## GPU Support

- GKE: comes w/ autoscaling GPU nodes
    - If you want to use, more than 1 P100 GPU, you will need to
      request a quota increase through the GCP Console.
- AKS: does not come w/ multiple autoscaling GPU node pools
    - To add a GPU node pool, run the following command
        ```
        az aks nodepool add \
                --resource-group <YOUR_RESOURCE_GROUP> \
                --cluster-name <YOUR_CLUSTER_NAME> \
                --name gpupool \
                --node-count <NUM_NODES_DESIRED> \
                --node-vm-size Standard_NC6  # or another GPU-accelerated node type.
        kubectl apply -f https://raw.githubusercontent.com/NVIDIA/k8s-device-plugin/master/nvidia-device-plugin.yml
        ```
    - To delete the GPU node pool, run the following:
        ```
        az aks nodepool delete -g <YOUR_RESOURCE_GROUP> --cluster-name <YOUR_CLUSTER_NAME> --name gpupool --no-wait
        ```
- Minikube: Can manually set up [GPUs](https://github.com/kubernetes/minikube/blob/master/docs/gpu.md) for Linux only

## Deleting a Cluster

- AKS: Run `az group delete --name <RESOURCE_GROUP> --yes --no-wait` where <RESOURCE_GROUP>
  is the resource group name of the cluster.
- GKE: Run `gcloud container clusters delete <CLUSTER_NAME> --async` where <CLUSTER_NAME> is
  the name of the cluster you would like to delete.
    - Also run `gcloud compute disks list` to make sure that all disks associated with the cluster have been deleted.
- EKS: Through the web UI, delete the EKS cluster, CloudFormation stack, IAM role,
  and misc. EC2 resources (load balancers, volumes).