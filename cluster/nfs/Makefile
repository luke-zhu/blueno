create:
	helm install stable/nfs-server-provisioner --name blueno-nfs \
		--set persistence.enabled=true,persistence.size=200Gi
	kubectl create -f pvc.yaml

delete:
	kubectl delete -f pvc.yaml
	helm delete blueno-nfs --purge