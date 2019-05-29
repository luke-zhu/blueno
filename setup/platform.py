"""
Script for setting up platform apps on an existing K8 cluster.

This file also contains methods shared by all cluster setup scripts.
"""
import os
import shutil
import subprocess


def set_script_cwd():
    filepath = os.path.realpath(__file__)
    path_parts = filepath.split('/')
    desired_path = '/'.join(path_parts[0:-2])
    print(f"Setting working directory to {desired_path}")
    os.chdir(desired_path)


def _configure_helm():
    if shutil.which('helm') is None:
        print("The Helm CLI is required but was not found!\n"
              "Installation details are available at "
              "https://github.com/helm/helm#install")
        exit(1)

    print("Configuring helm...")
    subprocess.check_call(
        'kubectl apply -f cluster/helm/rbac.yaml',
        shell=True,
    )
    subprocess.check_call(
        'helm init --service-account tiller --wait',
        shell=True,
    )
    subprocess.check_call(
        'helm repo update',
        shell=True,
    )


def setup_platform():
    """
    Sets up the platform applications on the kubernetes cluster that
    kubectl is connected to.

    After this one should be able to view the UI from the external IP
    of the nginx load balancer. In addition, one should be able to
    use the Platform the after manually creating a database user.

    This sets up a non-HTTP ingress.
    """
    _configure_helm()

    print('Setting up NFS...')
    subprocess.check_call(
        'make -C cluster/nfs create',
        shell=True,
    )

    print("Deploying the database...")
    subprocess.check_call(
        'make -C cluster/db create',
        shell=True,
    )

    print("Deploying the server...")
    subprocess.check_call(
        'make -C cluster/server create',
        shell=True,
    )

    print('Setting up ingress...')
    subprocess.check_call(
        'make -C cluster/ingress create',
        shell=True,
    )


if __name__ == '__main__':
    set_script_cwd()
    setup_platform()
