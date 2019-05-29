import logging
import sys
import time

from google.api_core.exceptions import FailedPrecondition
from google.cloud import container_v1
from kubernetes import client, config
from kubernetes.client.rest import ApiException

NONSCALABLE_APPS = [
    'blueno-nfs-nfs-server-provisioner-0',
]

OTHER_APPS = [
    'blueno-server',
    'blueno-db',
    'blueno-worker',
    'blueno-task-queue',
    'blueno-nginx-nginx-ingress-controller',
    'blueno-nginx-nginx-ingress-default-backend',
    'metabase',
    'mlflow',
    'night-scale-down',
    'morning-scale-up',
]

PLATFORM_APPS = OTHER_APPS + NONSCALABLE_APPS


def scale_up():
    # Called in the morning.
    apps_client = client.AppsV1Api()
    zerod_apps = set()
    deployments: client.V1DeploymentList = \
        apps_client.list_namespaced_deployment('default')
    dep: client.V1Deployment
    for dep in deployments.items:
        if dep.spec.replicas == 0:
            zerod_apps.add(dep.metadata.name)
    for app in PLATFORM_APPS:
        if app in NONSCALABLE_APPS:
            continue
        if app in zerod_apps:
            logging.info(f'Scaling up {app} to 1 replica')
            apps_client.patch_namespaced_deployment_scale(app, 'default', {
                'spec': {'replicas': 1}})
        else:
            logging.info(f'Not adjusting {app}')


def scale_down():
    # Called at night

    # 1. Check whether we should scale down.
    core_client = client.CoreV1Api()
    pods: client.V1PodList = core_client.list_namespaced_pod('default')

    pod: client.V1Pod
    for pod in pods.items:
        pod_name: str = pod.metadata.name
        if pod.status.phase != 'Running':
            logging.info(f'Ignoring {pod_name} with phase {pod.status.phase}')
            continue

        if not any(
                [pod_name.startswith(app_name) for app_name in PLATFORM_APPS]):
            logging.info(f'Non-platform {pod_name} is still running,'
                         f' not scaling down the cluster')
            return

    # 2. Scale down apps
    logging.info('Deleting all autoscalers')
    auto_client = client.AutoscalingV1Api()
    autoscalers: client.V1HorizontalPodAutoscalerList = \
        auto_client.list_namespaced_horizontal_pod_autoscaler('default')
    a: client.V1HorizontalPodAutoscaler
    for a in autoscalers.items:
        name = a.metadata.name
        logging.info(f'Deleting autoscaler {name}')
        auto_client.delete_namespaced_horizontal_pod_autoscaler(
            name, 'default')

    logging.info('Scaling down platform apps')
    apps_client = client.AppsV1Api()
    zero_spec = {
        'spec': {
            'replicas': 0,
        }
    }
    for app in PLATFORM_APPS:
        if app in NONSCALABLE_APPS:
            continue
        try:
            logging.info(f'Scaling down {app}')
            apps_client.patch_namespaced_deployment_scale(app,
                                                          'default',
                                                          zero_spec)
        except ApiException as e:
            logging.info(e)  # Likely app doesn't exist

    logging.info('Sleeping for 10s to allow nodes to terminate first')
    time.sleep(10)

    # 3. Scale down the cluster.
    # TODO: This section doesn't work at the moment
    # gke_client = container_v1.ClusterManagerClient()
    # res = gke_client.list_node_pools() # TODO:
    # for pool in res.node_pools:
    #     if pool.name != 'default-pool':
    #         for i in range(10):
    #             try:
    #                 logging.info(f'Resizing {pool.name}')
    #                 # TODO: replace ''
    #                 gke_client.set_node_pool_size('', '', '', pool.name,0)
    #                 break
    #             except FailedPrecondition as e:
    #                 logging.info(
    #                       f'Exception while resizing {pool.name}: {e}')
    #                 time.sleep(2 ** i)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    config.load_incluster_config()
    if sys.argv[1] == 'morning':
        scale_up()
    elif sys.argv[1] == 'night':
        scale_down()
