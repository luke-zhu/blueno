import signal
import subprocess
import time
from typing import List

import argparse


def create():
    subprocess.check_call('make -C nfs create', shell=True)
    subprocess.check_call('make -C db create', shell=True)
    subprocess.check_call('make -C server create', shell=True)
    subprocess.check_call('make -C ingress create', shell=True)


def delete():
    # Delete in reverse order to avoid blocking problem
    subprocess.check_call('make -C ingress delete', shell=True)
    subprocess.check_call('make -C server delete', shell=True)
    subprocess.check_call('make -C db delete', shell=True)
    subprocess.check_call('make -C nfs delete', shell=True)


def _blueno_server_pod_name() -> str:
    """
    Returns the name of the blueno server pod.
    """
    for i in range(100):
        out_bytes: bytes = subprocess.check_output(
            ('kubectl get pods'
             ' -o custom-columns=:metadata.name'
             ' --field-selector=status.phase=Running'),
            shell=True,
        )
        pods: List[str] = out_bytes.decode().split('\n')
        for pod in pods:
            if pod.startswith('blueno-server'):
                return pod
        time.sleep(5)
    raise RuntimeError(
        "Failed to find running 'blueno-server' pod in 100 tries")


def test():
    subprocess.check_call(f'flake8 --exclude node_modules,register.py',
                          shell=True)
    create()
    signal.signal(signal.SIGINT, delete)  # cleanup when ctrl-C is called

    try:
        pod = _blueno_server_pod_name()
        subprocess.check_call(
            (f'kubectl exec -it {pod}'
             ' -- pip install pytest pytest-cov testing.postgresql'),
            shell=True)
        subprocess.check_call(
            f'kubectl exec -it {pod} -- pytest --cov=app /server/app/',
            shell=True)
    finally:
        delete()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command')
    args = parser.parse_args()
    if args.command == 'create':
        create()
    elif args.command == 'delete':
        delete()
    elif args.command == 'test':
        test()
    else:
        raise ValueError(f"Command '{args.command} not found")
