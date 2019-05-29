"""
This script creates a Kubernetes cluster on Azure Kubernetes
Service (AKS) with the platform applications deployed.

To see the available configuration options, type in

    python scripts/setup_aks_cluster.py -h

or check CLIArguments and parse_cli() in the code below.
"""
import argparse
import shutil
import subprocess
import time

from platform import (
    set_script_cwd,
    setup_platform,
)


class AzureArguments:
    def __init__(self,
                 resource_group: str,
                 location: str,
                 cluster: str):
        self.resource_group = resource_group
        self.location = location
        self.cluster = cluster


def add_azure_args(parser: argparse.ArgumentParser):
    parser.add_argument('--resource-group',
                        default='blueno',
                        help='The Azure resource group to deploy the'
                             ' cluster in.')
    parser.add_argument('--location',
                        default='westus2',
                        help='The Azure region to deploy to.')
    parser.add_argument('--cluster',
                        default='blueno',
                        help='The name of the cluster to be created')


def parse_cli() -> AzureArguments:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    add_azure_args(parser)
    args = parser.parse_args()

    return AzureArguments(args.resource_group,
                          args.location,
                          args.cluster)


def create_aks_cluster(args: AzureArguments):
    if shutil.which('az') is None:
        print("The Azure CLI is required but was not found!\n"
              "Installation details are available at "
              "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli")
        exit(1)

    # Commands from
    # https://docs.microsoft.com/en-us/azure/aks/use-multiple-node-pools
    print('Enabling cluster autoscaling and multiple node pools')
    subprocess.check_call('az extension add --name aks-preview', shell=True)
    subprocess.check_call('az feature register'
                          ' --name MultiAgentpoolPreview'
                          ' --namespace Microsoft.ContainerService',
                          shell=True)
    subprocess.check_call(
        ('az feature register'
         ' --name VMSSPreview'
         ' --namespace Microsoft.ContainerService'),
        shell=True)
    for i in range(100):
        out = subprocess.check_output('az feature list -o table'
                                      ' --query "[?contains(name, \'Microsoft.ContainerService/VMSSPreview\')].{Name:name,State:properties.state}"',
                                      # noqa: E501
                                      shell=True)
        if 'Registering' in out.decode() or 'NotRegistered' in out.decode():
            time.sleep(10)
            continue
        out = subprocess.check_output('az feature list -o table'
                                      ' --query "[?contains(name, \'Microsoft.ContainerService/MultiAgentpoolPreview\')].{Name:name,State:properties.state}"',
                                      # noqa: E501
                                      shell=True)
        if 'Registering' in out.decode() or 'NotRegistered' in out.decode():
            time.sleep(10)
            continue
        # At this point, both features are registered
        break
    else:
        raise RuntimeError(
            "Failed to register Microsoft.ContainerService/VMSSPreview"
            " in 100 tries")
    subprocess.check_call(
        'az provider register --namespace Microsoft.ContainerService',
        shell=True)

    print(f"Creating an Azure resource group named {args.resource_group}...")
    subprocess.check_call(
        [
            'az', 'group', 'create',
            '--name', args.resource_group,
            '--location', args.location,
        ],
    )
    print(f"Creating an AKS cluster named {args.cluster}...")
    subprocess.check_call(
        [
            "az", "aks", "create",
            "--resource-group", args.resource_group,
            "--name", args.cluster,
            "--location", args.location,
            "--node-count", '1',
            "--enable-vmss",
            "--enable-cluster-autoscaler",
            "--min-count", "1",
            "--max-count", "10"
        ],
    )

    print("Configuring kubectl...")
    subprocess.check_call(
        [
            'az', 'aks', 'get-credentials',
            '--resource-group', args.resource_group,
            '--name', args.cluster,
            # See https://github.com/Azure/azure-cli/issues/7670
            # for why we use this flag.
            '--overwrite-existing'
        ],
    )


if __name__ == '__main__':
    set_script_cwd()
    az_args = parse_cli()
    create_aks_cluster(az_args)
    setup_platform()
    print("All done!")
