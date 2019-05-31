# Keep the image name in-sync with the k8s config files
image = cyclotomic/blueno-server

create:
	sed s/YOUR_JWT_KEY_HERE/$(shell head -c 24 /dev/random | base64 | tr -dc A-Za-z0-9)/g \
			k8s/secrets.yaml | kubectl create -f -
	kubectl create -f k8s/server.yaml,k8s/task-queue.yaml,k8s/worker.yaml

delete:
	kubectl delete -f k8s/secrets.yaml,k8s/server.yaml,k8s/task-queue.yaml,k8s/worker.yaml

push-image:
	docker build -f docker/prod/Dockerfile -t $(image) .
	docker push $(image)

pod := $(shell kubectl get pods -o custom-columns=:metadata.name --field-selector=status.phase=Running | grep blueno-server)
shell:
	kubectl exec -it $(pod) -- /bin/bash

env_vars := FILESYSTEM_STORE_ROOT=test_data_dir
# Test the server locally without docker
test:
	${env_vars} pytest --cov=app --cov-report html app/