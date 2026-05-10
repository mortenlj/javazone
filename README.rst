=========================
JavaZone calendar manager
=========================

A simple application that will help manager your JavaZone experience.

-------
Concept
-------

You add a JavaZone talk (using its session ID) to your account, and you get a calendar invite to that session.
If the session changes, you get calendar updates automatically.

-----------
Development
-----------

We use mise_ (with mise-lib_) to manage tool versions, development tasks and building.

Various useful commands:

Reseal the secret by connecting to the current cluster context and running kubeseal
-----------------------------------------------------------------------------------

``mise run reseal-secret``

Assemble the deploy manifests
-----------------------------

``mise run k8s:manifests``

Build the docker image
----------------------

``mise run docker``



.. _mise: https://mise.jdx.dev
.. _mise-lib: https://github.com/mortenlj/mise-lib
