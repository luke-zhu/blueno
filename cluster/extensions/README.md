This directory currently contains code for deploying other open-source applications


- `make jupyter`: start a CPU-only Jupyter notebook
- `make jupyter-gpu`: start a GPU-accelerated Jupyter notebook
- `make gke-downscale`: scale down the GKE cluster to 1 g1-micro VM at 5pm and scale it back up at 9am
    - This requires you to make a service account with GKE admin access and register the secret `gke-service-account`.
      Rename the file to `gke.json` before creating the key.
- `make mlflow`: start an Mlflow Tracking server
- `make metabase`: start a Metabase dashboard