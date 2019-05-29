"""
This script creates a Kubernetes cluster on Google Kubernetes
Engine (GKE) with the platform applications deployed.
"""
import argparse
import subprocess

from platform import (
    set_script_cwd,
    setup_platform
)


class GCloudArguments:
    def __init__(self,
                 zone: str,
                 cluster: str):
        self.zone = zone
        self.cluster = cluster


def add_gcloud_args(parser: argparse.ArgumentParser):
    parser.add_argument('--zone',
                        default='us-west1-b',
                        help='The GCP zone to deploy the cluster in')
    parser.add_argument('--cluster',
                        default='blueno',
                        help='The name of the cluster to be created')


def parse_cli() -> GCloudArguments:
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    add_gcloud_args(parser)
    args = parser.parse_args()
    return GCloudArguments(zone=args.zone,
                           cluster=args.cluster)


def create_gke_cluster(args: GCloudArguments):
    subprocess.check_call(
        (f'gcloud container clusters create {args.cluster}'
         f' --zone {args.zone}'
         ' --machine-type g1-small'
         ' --disk-size 30GB'
         ' --num-nodes 1'),
        shell=True)

    subprocess.check_call(
        ('gcloud container node-pools create n1-standard-2'
         f' --cluster {args.cluster}'
         f' --zone {args.zone}'
         ' --machine-type n1-standard-2'
         ' --disk-size 30GB'
         ' --num-nodes 1'
         ' --enable-autoscaling'
         ' --min-nodes 0'
         ' --max-nodes 10'),
        shell=True
    )

    subprocess.check_call(
        (f'gcloud container clusters get-credentials {args.cluster}'
         f' --zone {args.zone}'),
        shell=True,
    )


if __name__ == '__main__':
    set_script_cwd()
    gcloud_args = parse_cli()
    create_gke_cluster(gcloud_args)
    setup_platform()

    print("Adding the GPU node pool")
    subprocess.check_call(
        ('gcloud container node-pools create n1-standard-2-p100'
         f' --cluster {gcloud_args.cluster}'
         f' --zone {gcloud_args.zone}'
         ' --machine-type n1-standard-2'
         ' --disk-size 30GB'
         ' --accelerator type=nvidia-tesla-p100'
         ' --num-nodes 0'
         ' --enable-autoscaling'
         ' --min-nodes 0'
         ' --max-nodes 10'),
        shell=True
    )
    subprocess.check_call(
        ('kubectl apply -f https://raw.githubusercontent.com/'
         'GoogleCloudPlatform/container-engine-accelerators/stable/'
         'nvidia-driver-installer/cos/daemonset-preloaded.yaml'),
        shell=True)
    print("All done!")
