# JavaZone calendar manager

A simple application that will help manager your JavaZone experience.

## Concept

You add a JavaZone talk (using its session ID) to your account, and you get a calendar invite to that session.
If the session changes, you get calendar updates automatically.


## Development

We use [`earthly`](https://earthly.dev) for building.
If you don't have earthly installed, you can use the wrapper [`earthlyw`](https://github.com/mortenlj/earthlyw) in the root of the repository.

Build docker image: `./earthlyw +docker`
Run prospector and pytest: `./earthlyw +test`
