mlflow_image = cyclotomic/mlflow
gke_downscale_image = cyclotomic/gke-downscale

.PHONY: jupyter jupyter-gpu metabase mlflow gke-downscale

jupyter:
	kubectl apply -f jupyter/

jupyter-gpu:
	kubectl apply -f jupyter-gpu/

metabase:
	echo "CREATE DATABASE metabase;" | make -C ../db psql
	kubectl apply -f metabase/

push-mlflow:
	docker build -f mlflow/Dockerfile -t $(mlflow_image) .
	docker push $(mlflow_image)

mlflow:
	echo "CREATE DATABASE mlflow;" | make -C ../db psql
	kubectl apply -f mlflow/

push-gke-downscale:
	docker build  -f gke-downscale/Dockerfile -t $(gke_downscale_image) ./gke-downscale
	docker push $(gke_downscale_image)

gke-downscale:
	kubectl apply -f gke-downscale/