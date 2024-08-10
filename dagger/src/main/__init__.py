import asyncio

from itertools import chain

import dagger
from dagger import dag, function, object_type


@object_type
class Javazone:
    @function
    def deps(self, source: dagger.Directory, platform: dagger.Platform | None = None) -> dagger.Container:
        """Install dependencies in a container"""
        return (
            dag.container(platform=platform)
            .from_("python:3.12-slim")
            .with_workdir("/app")
            .with_exec(["pip", "install", "poetry"])
            .with_env_variable("POETRY_VIRTUALENVS_IN_PROJECT", "true")
            .with_file("/app/pyproject.toml", source.file("pyproject.toml"))
            .with_file("/app/poetry.lock", source.file("poetry.lock"))
            .with_exec(
                ["poetry", "install", "--only", "main", "--no-root", "--no-interaction"]
            )
        )

    @function
    def build(self, source: dagger.Directory, platform: dagger.Platform | None = None) -> dagger.Container:
        """Build the application"""
        return (
            self.deps(source, platform)
            .with_file("/app/.prospector.yaml", source.file(".prospector.yaml"))
            .with_directory("/app/javazone", source.directory("javazone"))
            .with_directory("/app/tests", source.directory("tests"))
            .with_exec(["poetry", "install", "--no-interaction"])
            .with_exec(["poetry", "run", "black", "--check", "."])
            .with_exec(["poetry", "run", "prospector"])
            .with_exec(["poetry", "run", "pytest"])
        )

    @function
    def docker(self, source: dagger.Directory, platform: dagger.Platform | None = None) -> dagger.Container:
        """Build the Docker container"""
        deps = self.deps(source, platform)
        src = self.build(source, platform)
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
    async def publish(self, source: dagger.Directory, image: str = "ttl.sh/mortenlj-javazone", version: str = "develop") -> list[str]:
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
                variants.append(self.docker(source, platform))
            cos.append(manifest.publish(f"{image}:{v}", platform_variants=variants))

        return await asyncio.gather(*cos)

    @function
    async def deploy(self, source: dagger.Directory, image: str = "ttl.sh/mortenlj-javazone", version: str = "develop") -> list[str]:
        """Build and assemble deployable artifacts"""
        publishing_co = self.publish(source, image, version)
        # TODO: Assemble manifests
        # manifests_co = self.assemble_manifests(source, image, version)

        results = await asyncio.gather(publishing_co)
        return list(chain.from_iterable(results))
