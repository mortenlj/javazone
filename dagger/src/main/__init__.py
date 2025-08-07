import asyncio
import textwrap
import toml
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

    async def resolve_python_version(self) -> str:
        """Resolve the Python version"""
        contents = await self.source.file("pyproject.toml").contents()
        pyproject = toml.loads(contents)
        py_version = pyproject["project"]["requires-python"]
        return py_version[2:]

    async def install_mise(self, container: dagger.Container, *tools) -> dagger.Container:
        """Install Mise in a container, and install tools"""
        installer = dag.http("https://mise.run")
        return (
            container.with_exec(["apt-get", "update", "--yes"])
            .with_exec(["apt-get", "install", "--yes", "curl"])
            .with_env_variable("MISE_DATA_DIR", "/mise")
            .with_env_variable("MISE_CONFIG_DIR", "/mise")
            .with_env_variable("MISE_CACHE_DIR", "/mise/cache")
            .with_env_variable("MISE_INSTALL_PATH", "/usr/local/bin/mise")
            .with_env_variable("PATH", "/mise/shims:${PATH}", expand=True)
            .with_new_file("/usr/local/bin/mise-installer", await installer.contents(), permissions=755)
            .with_exec(["/usr/local/bin/mise-installer"])
            .with_exec(["mise", "trust", "/app/mise.toml"])
            .with_file("/app/mise.toml", self.source.file(".config/mise/config.toml"))
            .with_exec(["mise", "install", *tools])
        )

    @function
    async def deps(self, platform: dagger.Platform | None = None) -> dagger.Container:
        """Install dependencies in a container"""
        python_version = await self.resolve_python_version()
        base_container = dag.container(platform=platform).from_(f"python:{python_version}-slim").with_workdir("/app")
        return (
            (await self.install_mise(base_container, "uv"))
            .with_file("/app/pyproject.toml", self.source.file("pyproject.toml"))
            .with_file("/app/uv.lock", self.source.file("uv.lock"))
            .with_exec(["uv", "sync", "--no-install-workspace", "--locked", "--compile-bytecode"])
        )

    @function
    async def build(self, platform: dagger.Platform | None = None) -> dagger.Container:
        """Build the application"""
        return (
            (await self.deps(platform))
            .with_file("/app/.prospector.yaml", self.source.file(".prospector.yaml"))
            .with_directory("/app/javazone", self.source.directory("javazone"))
            .with_directory("/app/tests", self.source.directory("tests"))
            .with_exec(["uv", "sync", "--locked", "--compile-bytecode", "--group=dev"])
            .with_exec(["uv", "run", "black", "--check", "."])
            .with_exec(["uv", "run", "prospector"])
            .with_exec(["uv", "run", "pytest"])
        )

    @function
    async def docker(self, platform: dagger.Platform | None = None) -> dagger.Container:
        """Build the Docker container"""
        python_version = await self.resolve_python_version()
        deps = await self.deps(platform)
        src = await self.build(platform)
        return (
            dag.container(platform=platform)
            .from_(f"python:{python_version}-slim")
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
            cos.append(manifest.publish(f"{image}:{v}", platform_variants=await asyncio.gather(*variants)))

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
        return await self.source.with_new_file("deploy.yaml", "\n".join(documents)).file("deploy.yaml")

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
