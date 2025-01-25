import asyncio
import textwrap
from typing import Annotated

import dagger
from dagger import dag, function, object_type, DefaultPath, Ignore, Doc
from jinja2 import Template

RESEAL_SCRIPT = textwrap.dedent(
    """\
    #!/bin/bash
    
    echo "---" > sealed-secret.yaml
    kubectl create secret generic --dry-run=client --namespace default -ojson javazone --from-env-file=.env | \
        jq '.metadata.labels.app="javazone"' | \
        kubeseal -ojson | \
        jq '.metadata.labels.app="javazone"' | \
        yq -Poyaml >> sealed-secret.yaml
"""
)


@object_type
class Javazone:
    source: Annotated[dagger.Directory, DefaultPath("/"), Ignore(["target", ".github", "dagger", ".idea"])]

    @function
    def deps(self, platform: dagger.Platform | None = None) -> dagger.Container:
        """Install dependencies in a container"""
        return (
            dag.container(platform=platform)
            .from_("python:3.12-slim")
            .with_workdir("/app")
            .with_exec(["pip", "install", "poetry"])
            .with_env_variable("POETRY_VIRTUALENVS_IN_PROJECT", "true")
            .with_file("/app/pyproject.toml", self.source.file("pyproject.toml"))
            .with_file("/app/poetry.lock", self.source.file("poetry.lock"))
            .with_exec(["poetry", "install", "--only", "main", "--no-root", "--no-interaction"])
        )

    @function
    def build(self, platform: dagger.Platform | None = None) -> dagger.Container:
        """Build the application"""
        return (
            self.deps(platform)
            .with_file("/app/.prospector.yaml", self.source.file(".prospector.yaml"))
            .with_directory("/app/javazone", self.source.directory("javazone"))
            .with_directory("/app/tests", self.source.directory("tests"))
            .with_exec(["poetry", "install", "--no-interaction"])
            .with_exec(["poetry", "run", "black", "--check", "."])
            .with_exec(["poetry", "run", "prospector"])
            .with_exec(["poetry", "run", "pytest"])
        )

    @function
    def docker(self, platform: dagger.Platform | None = None) -> dagger.Container:
        """Build the Docker container"""
        deps = self.deps(platform)
        src = self.build(platform)
        return (
            dag.container(platform=platform)
            .from_("python:3.12-slim")
            .with_workdir("/app")
            .with_directory("/app/.venv", deps.directory("/app/.venv"))
            .with_directory("/app/javazone", src.directory("/app/javazone"))
            .with_env_variable("PATH", "/app/.venv/bin:${PATH}", expand=True)
            .with_entrypoint(["/app/.venv/bin/python", "-m", "javazone"])
        )

    @function
    async def publish(self, image: str = "ttl.sh/mortenlj-javazone", version: str = "develop") -> list[str]:
        """Publish the application container after building and testing it on-the-fly"""
        platforms = [
            dagger.Platform("linux/amd64"),  # a.k.a. x86_64
            dagger.Platform("linux/arm64"),  # a.k.a. aarch64
        ]
        cos = []
        manifest = dag.container()
        for v in ["latest", version]:
            variants = []
            for platform in platforms:
                variants.append(self.docker(platform))
            cos.append(manifest.publish(f"{image}:{v}", platform_variants=variants))

        return await asyncio.gather(*cos)

    @function
    async def assemble_manifests(
        self, image: str = "ttl.sh/mortenlj-javazone", version: str = "develop"
    ) -> dagger.File:
        """Assemble manifests"""
        template_dir = self.source.directory("deploy")
        documents = []
        for filepath in await template_dir.entries():
            src = await template_dir.file(filepath).contents()
            if not filepath.endswith(".j2"):
                contents = src
            else:
                template = Template(src, enable_async=True)
                contents = await template.render_async(image=image, version=version)
            if contents.startswith("---"):
                documents.append(contents)
            else:
                documents.append("---\n" + contents)
        return await source.with_new_file("deploy.yaml", "\n".join(documents)).file("deploy.yaml")

    @function
    async def reseal_secret(
        self, kubeconfig: Annotated[dagger.Secret, Doc("kubeconfig file for the cluster")]
    ) -> dagger.File:
        """Reseal the secret, using the kubeconfig file for the cluster"""
        return await (
            dag.container()
            .from_("ghcr.io/mortenlj/kafka-debug:latest")
            .with_workdir("/reseal")
            .with_new_file("/root/.kube/config", await kubeconfig.plaintext())
            .with_new_file("reseal.sh", RESEAL_SCRIPT)
            .with_file(".env", self.source.file(".env"))
            .with_exec(["bash", "reseal.sh"])
            .file("sealed-secret.yaml")
        )
