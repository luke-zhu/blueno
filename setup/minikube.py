"""
This script creates a minikube cluster with the platform applications
deployed.
"""
import shutil
import subprocess

from platform import (
    setup_platform,
    set_script_cwd
)


def create_minikube_cluster():
    if shutil.which('minikube') is None:
        print("Minikube was not found. Installation details are available at"
              " https://kubernetes.io/docs/tasks/tools/install-minikube/")
        exit(1)

    print("Starting minikube cluster")
    subprocess.check_call(
        'minikube start --memory 4096 --disk-size 20000MB',
        shell=True,
    )


if __name__ == '__main__':
    set_script_cwd()
    create_minikube_cluster()
    setup_platform()
    print("All done!")
