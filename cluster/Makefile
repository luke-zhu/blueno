create:
	python3 ./cli.py create

delete:
	python3 ./cli.py delete

# Use this command to develop the platform.
# This platform starts up the platform applications, rebuilding and/or restarting
# the images when code is changed in any of the directories.
dev:
	# To install skaffold on OS X, run `brew install skaffold`
	skaffold dev --port-forward

# Runs the platform apps on the cluster and tests that the server tests pass
test:
	python3 ./cli.py test