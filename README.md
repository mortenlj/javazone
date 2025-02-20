# JavaZone calendar manager

A simple application that will help manager your JavaZone experience.

## Concept

You add a JavaZone talk (using its session ID) to your account, and you get a calendar invite to that session.
If the session changes, you get calendar updates automatically.


## Development

We use [`dagger`](https://dagger.io) for building, and mise to manage tool versions and development tasks.

Various useful commands:

### Reseal the secret by connecting to the current cluster context and running kubeseal

    `dagger call reseal-secret --kubeconfig=file:~/.kube/config --output=deploy/sealed-secret.yaml`

### Assemble the deploy manifests

    `dagger call assemble-manifests "--image=${IMAGE}" "--version=${VERSION}" --output=deploy.yaml`

### Build the docker image

    `dagger call publish "--image=${IMAGE}" "--version=${VERSION}"`
