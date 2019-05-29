create:
	# The command below creates the config with a random password.
	sed s/YOUR_PASSWORD_HERE/$(shell head -c 24 /dev/random | base64 | tr -dc A-Za-z0-9)/g \
		k8s/config.yaml | kubectl create -f -
	kubectl create -f k8s/app.yaml

# WARNING: this command removes all blueno-db resources, including the database data.
delete:
	kubectl delete -f k8s/config.yaml,k8s/app.yaml

# Starts a psql shell connected to the blueno database
pod := $(shell kubectl get pods -o custom-columns=:metadata.name --field-selector=status.phase=Running | grep blueno-db)
psql:
	kubectl exec -it $(pod) -- \
		/bin/bash -c 'PGPASSWORD="$${POSTGRES_PASSWORD}" psql -U "$${POSTGRES_USER}" -d "$${POSTGRES_DB}"'