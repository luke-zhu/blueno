This directory contains for applications that run
on the Kubernetes cluster.

Here is a brief overview of what the major subdirectories contain:

- `db`: The database configuration code
    - Calling `make psql` from this directory will connect you to the database.
- `extensions` - `make` commands to deploy various ML tools
- `ingress` - The NGINX ingress configuration. See [ingress/README.md](./ingress/README.md)
  for more information on how to set up HTTPS and expose more applications.
- `nfs` - The NFS configuration. See [nfs/README.md](./nfs/README.md)
  for more information on how to resize the NFS volume.
- `server` - The Blueno server code. See [server/README.md](./server/README.md) for more info.

This directory also contains a `Makefile` for deploying, deleting, and testing the applications.