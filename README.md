# JavaZone calendar manager

A simple application that will help manager your JavaZone experience.

## Concept

You add a JavaZone talk (using its session ID) to your account, and you get a calendar invite to that session.
If the session changes, you get calendar updates automatically.


## Development

We use [`dagger`](https://dagger.io) for building.

Various useful commands:

### Reseal the secret by connecting to the current cluster context and running kubeseal

    `dagger call reseal-secret --source=. --kubeconfig=file:~/.kube/config --output=deploy/sealed-secret.yaml`

### Assemble the deploy manifests

    `dagger call assemble-manifests --source=. "--image=${IMAGE}" "--version=${VERSION}" --output=deploy.yaml`

### Build the docker image

    `dagger call publish --source=. "--image=${IMAGE}" "--version=${VERSION}"`
