#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "invoke-toolkit>=0.0.73",
# ]
# ///
"""Development tasks for the workshop slides."""

import json
import os
import re
import shlex
import shutil
import urllib.request
from datetime import date
from html import escape
import webbrowser
from pathlib import Path
from typing import Annotated, Union, cast
from urllib.parse import unquote, urlsplit

import yaml
from invoke_toolkit import Context, script, task, Task
from invoke_toolkit.utils.fzf import select

ROOT = Path(__file__).resolve().parent
SLIDES = ROOT / "slides.qmd"
SLIDES = SLIDES.relative_to(ROOT)


@task()
def _quarto_installed(ctx: Context):
    if not shutil.which("quarto"):
        ctx.rich_exit("quarto not found in [red]$PATH[/]")


@task()
def free_port(ctx: Context, port: int, status: str = "listen") -> None:
    """Free a port"""
    if not isinstance(port, int) or not 1024 < port < 65535:
        ctx.rich_exit("Port is invalid")
    ctx.run(f"lsof -i :{port} | grep {{status}} | awk '{{print $2}}' | xargs kill -9")


@task(aliases=["p"], pre=[_quarto_installed])
def preview(
    ctx: Context,
    port: Annotated[
        Union[int, str], "Local preview port; 0 lets Quarto choose"
    ] = "$PORT",
    host: Annotated[str, "Interface on which to serve the preview"] = "127.0.0.1",
    no_browser: Annotated[bool, "Do not open the preview in a browser"] = False,
    kill_others: Annotated[bool, "Kill other servers in the same port"] = True,
) -> None:
    """Render and serve the Reveal.js deck with live reload."""
    command = f"""
        quarto preview {SLIDES} --render revealjs --host {host} \
        {f"--port {port}" if port else ""} \
        {"--no-browser" if no_browser else ""}
        """
    if kill_others:
        ctx.run(f"lsof -i :{port} | tail -n1 | awk '{{print $2}}' | xargs kill -9")

    with ctx.cd(ROOT):
        ctx.run(command, pty=True)


@task(aliases=["r"])
def render(ctx: Context) -> None:
    """Render the Reveal.js deck into _site/slides.html."""
    command = ["quarto", "render", str(SLIDES), "--to", "revealjs"]
    with ctx.cd(ROOT):
        ctx.run(shlex.join(command))


@task(aliases=["o"])
def open_slides(ctx: Context, port: str | int = ""):
    """Open the browser in a particular port (for slide preview)"""
    port = port if port else os.getenv("PORT", 0)
    webbrowser.open(f"http://localhost:{port}")


def _service_urls() -> dict[str, str]:
    """Return host URLs for Compose services with published ports."""
    compose = yaml.safe_load((ROOT / "compose.yaml").read_text())
    services = compose.get("services", {})
    urls: dict[str, str] = {}

    for service_name, service in services.items():
        for port in service.get("ports", []):
            published_port = None
            if isinstance(port, str):
                # Compose accepts HOST:CONTAINER and IP:HOST:CONTAINER.
                fields = port.split(":")
                if len(fields) >= 2:
                    published_port = fields[-2]
            elif isinstance(port, dict):
                published_port = port.get("published")

            if published_port not in (None, 0, "0"):
                urls[service_name] = f"http://127.0.0.1:{published_port}"
                break

    return urls


@task(positional=["service_slug"])
def open_service(
    ctx: Context,
    service_slug: Annotated[str, "Service to open; omit to select interactively"] = "",
) -> None:
    """Open a Compose service with a published port in the system browser."""
    service_urls = _service_urls()
    if not service_urls:
        ctx.rich_exit("No Compose services have a published port.", exit_code=1)

    selected_service = service_slug or cast(
        str | None,
        select(
            ctx,
            list(service_urls),
            prompt="Select a service to open",
            select_1=True,
        ),
    )
    if not selected_service:
        return
    if selected_service not in service_urls:
        ctx.rich_exit(f"Unknown service: {selected_service}", exit_code=1)

    opener = shutil.which("xdg-open") or shutil.which("open")
    if opener is None:
        ctx.rich_exit("Could not find xdg-open or open on this system.", exit_code=1)

    ctx.run(shlex.join([opener, service_urls[selected_service]]))


@task(aliases=["hermes"])
def setup_hermes(
    ctx: Context,
    model: Annotated[str, "OpenRouter model ID"] = "deepseek/deepseek-v4.1-flash",
) -> None:
    """Configure Hermes from OPENROUTER_API_KEY and restart Compose services."""
    if not os.environ.get("OPENROUTER_API_KEY"):
        ctx.rich_exit(
            "Set OPENROUTER_API_KEY in .env before running this task.", exit_code=1
        )
    if not model:
        ctx.rich_exit("A model ID is required.", exit_code=1)

    compose = ["docker", "compose"]
    with ctx.cd(ROOT):
        ctx.run(shlex.join([*compose, "stop", "hermes", "webui"]))
        ctx.run(
            shlex.join(
                [
                    *compose,
                    "run",
                    "--rm",
                    "--no-deps",
                    "hermes",
                    "config",
                    "set",
                    "model.provider",
                    "openrouter",
                ]
            )
        )
        ctx.run(
            shlex.join(
                [
                    *compose,
                    "run",
                    "--rm",
                    "--no-deps",
                    "hermes",
                    "config",
                    "set",
                    "model.default",
                    model,
                ]
            )
        )
        mcp_config = json.dumps(
            {
                "enabled": True,
                "command": "uvx",
                "args": ["--with", "fastmcp<3", "mcp-server-grist"],
                "env": {
                    "GRIST_API_KEY": "${GRIST_API_KEY}",
                    "GRIST_API_URL": "http://grist:8484/api",
                },
                "connect_timeout": 60,
                "timeout": 120,
            }
        )
        ctx.run(
            shlex.join(
                [
                    *compose,
                    "run",
                    "--rm",
                    "--no-deps",
                    "hermes",
                    "config",
                    "set",
                    "mcp_servers.grist",
                    mcp_config,
                ]
            )
        )
        ctx.run(shlex.join([*compose, "up", "-d", "hermes", "webui"]))
    ctx.print(f"Hermes configured for OpenRouter model: {model}")


@task(aliases=["models"])
def update_models(ctx: Context) -> None:
    """Fetch free OpenRouter models and generate the Caddy model catalog page."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        ctx.rich_exit(
            "Set OPENROUTER_API_KEY in .env before running this task.", exit_code=1
        )

    request = urllib.request.Request(
        "https://openrouter.ai/api/v1/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        catalog = json.load(response)

    models = [
        model
        for model in catalog["data"]
        if model["id"].endswith(":free")
        and model.get("context_length", 0) >= 64_000
        and "tools" in model.get("supported_parameters", [])
    ]
    models.sort(key=lambda model: model["id"])
    rows = "\n".join(
        "<tr><td><code>{}</code></td><td>{}</td><td>{:,}</td></tr>".format(
            escape(model["id"]),
            escape(model.get("name", "")),
            model["context_length"],
        )
        for model in models
    )
    generated = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Free Hermes Models</title>
<style>
body {{ margin: 0; padding: 2rem; font: 16px system-ui, sans-serif; background: #f7fafc; color: #1a202c; }}
main {{ max-width: 1100px; margin: auto; background: white; padding: 2rem; border-radius: 1rem; box-shadow: 0 8px 30px #0002; }}
a {{ color: #4c51bf; }} table {{ width: 100%; border-collapse: collapse; margin-top: 1.5rem; }}
th, td {{ text-align: left; padding: .75rem; border-bottom: 1px solid #e2e8f0; }} th {{ background: #edf2f7; }}
code {{ word-break: break-all; }} .meta {{ color: #718096; }}
</style></head><body><main>
<p><a href="/">← Workshop services</a></p>
<h1>Free OpenRouter models for Hermes</h1>
<p class="meta">Generated {date.today().isoformat()} · {len(models)} models · requires ≥64K context and tool support</p>
<table><thead><tr><th>Model ID</th><th>Name</th><th>Context</th></tr></thead><tbody>{rows}</tbody></table>
</main></body></html>
"""
    (ROOT / "caddy" / "models.html").write_text(generated, encoding="utf-8")
    ctx.print(f"Generated caddy/models.html with {len(models)} models")


_MARKDOWN_IMAGE = re.compile(
    r"!\[(?:[^\[\]]|\[[^\]]*\]\([^)]*\))*\]\(\s*<?([^\s)>]+)>?"
)


def _referenced_local_images() -> list[Path]:
    """Return existing repository files referenced as Markdown images."""
    images: set[Path] = set()
    for reference in _MARKDOWN_IMAGE.findall(SLIDES.read_text(encoding="utf-8")):
        parsed = urlsplit(reference)
        if parsed.scheme or parsed.netloc:
            continue

        path = (ROOT / SLIDES.parent / unquote(parsed.path)).resolve()
        try:
            relative_path = path.relative_to(ROOT)
        except ValueError:
            continue
        if path.is_file():
            images.add(relative_path)

    return sorted(images)


@task()
def stage_images(ctx: Context) -> None:
    """Stage local images referenced by slides.qmd."""
    images = _referenced_local_images()
    if not images:
        ctx.print("No local slide images found")
        return

    command = ["git", "add", "--", *(str(path) for path in images)]
    with ctx.cd(ROOT):
        ctx.run(shlex.join(command))
    ctx.print(f"Staged {len(images)} slide image(s)")


@task()
def unused_images(ctx: Context) -> None:
    """List files in img/ that are not referenced by slides.qmd."""
    referenced = set(_referenced_local_images())
    unused = sorted(
        path.relative_to(ROOT)
        for path in (ROOT / "img").iterdir()
        if path.is_file() and path.relative_to(ROOT) not in referenced
    )

    for path in unused:
        ctx.print(path)


def _ensure_tilt_installed(ctx: Context, fail: bool = False):
    """Check that tilt is installed"""
    if not shutil.which("tilt"):
        if fail:
            ctx.rich_exit("[red]tilt[/] not installed")
        else:
            ctx.print_error("tilt not found")


@task(
    pre=[
        Task(_ensure_tilt_installed),
    ]
)
def up(ctx: Context) -> None:
    """Shortcut for tilt up"""
    free_port(
        ctx,
        port=10350,
    )
    ctx.run("tilt up", pty=True)


@task()
def update(ctx: Context):
    """Update git and publish"""
    ctx.run("git add -u")
    ctx.run('git commit -m "Updates"')
    ctx.run("quarto publish gh-pages --no-prompt")


script()
