create:
	helm install stable/nginx-ingress --name blueno-nginx
	kubectl create -f ingress.yaml

delete:
	helm delete blueno-nginx --purge
	kubectl delete -f ingress.yaml
