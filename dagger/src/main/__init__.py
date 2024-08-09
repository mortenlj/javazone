import random

import dagger
from dagger import dag, function, object_type


@object_type
class Javazone:
    @function
    async def publish(self, source: dagger.Directory) -> str:
        """Publish the application container after building and testing it on-the-fly"""
        await self.test(source)
        return await self.build(source).publish(
            f"ttl.sh/mortenlj-javazone-{random.randrange(10 ** 8)}"
        )

    @function
    def build(self, source: dagger.Directory) -> dagger.Container:
        """Build the application container"""
        venv = (
            self.build_env(source)
            .directory("./.venv")
        )
        src = (
            self.build_env(source)
            .directory("./javazone")
        )
        return (
            dag.container()
            .from_("python:3.12-slim")
            .with_workdir("/app")
            .with_directory("/app/.venv", venv)
            .with_directory("/app/javazone", src)
            .with_exposed_port(3000)
            .with_env_variable("PATH", "/app/.venv/bin:${PATH}", expand=True)
            .with_entrypoint(["/app/.venv/bin/python", "-m", "javazone"])
        )

    @function
    async def test(self, source: dagger.Directory) -> str:
        """Return the result of running unit tests"""
        return await (
            self.build_env(source)
            .with_exec(["poetry", "run", "pytest"])
            .stdout()
        )

    @function
    def build_env(self, source: dagger.Directory) -> dagger.Container:
        """Build a ready-to-use development environment"""
        return (
            dag.container()
            .from_("python:3.12-slim")
            .with_directory("/src", source)
            .with_workdir("/src")
            .with_exec(["pip", "install", "poetry"])
            .with_env_variable("POETRY_VIRTUALENVS_IN_PROJECT", "true")
            .with_exec(["poetry", "install", "--no-interaction"])
        )
