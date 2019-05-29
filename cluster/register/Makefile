image = cyclotomic/blueno-registration-pipelines

push-image:
	docker build -t $(image) .
	docker push $(image)

submit-mnist:
	kubectl create -f k8s/mnist.yaml

delete-mnist:
	kubectl delete -f k8s/mnist.yaml

submit-imagenet:
	kubectl create -f k8s/imagenet.yaml

delete-imagenet:
	kubectl delete -f k8s/imagenet.yaml