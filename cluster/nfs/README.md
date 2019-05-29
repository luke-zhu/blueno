`make create` creates a NFS server and a 200 GiB persistent volume claim
with helm.

The NFS volume cannot be resized after setup without taking down the NFS
server privovisioner deployment first.

## Resizing the NFS volume

Resizing the volume is a manual process. You
may want to back up your data before executing this process.

1. Take down apps that rely on the NFS server. 
    - `kubectl scale --replicas=0 deployment/blueno-server deployment/blueno-worker`
    - Make sure no register jobs are running.
2. Run
      ```
      kubectl patch pv <DATA_PV_NAME> -p '{"spec":{"persistentVolumeReclaimPolicy":"Retain"}}'` so the data volume is not deleted.
      ```
3. Run `kubectl delete pvc blueno-nfs`, then `kubectl delete pvc data-blueno-nfs-nfs-server-provisioner-0`, and `helm delete blueno-nfs --purge`.
4. Run `helm delete blueno-nfs --purge`.
5. Change the disk size values in `Makefile` and `pvc.yaml` and recreate the resources
   `make create`.
6. Scale up the other applications.