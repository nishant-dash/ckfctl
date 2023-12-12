# ckfctl.
from ckfctl.ckf_upgrade_planner import CharmedKubeflowUpgradePlanner
from ckfctl.env_getter import get_env_proxy_vars
from ckfctl.prepare_node import prepare_node_script

# cli
import typer

# typing utils
from typing_extensions import Annotated
from typing import List

# console and formatting
from rich.console import Console
from rich.syntax import Syntax


cli = typer.Typer(
    name="ckfctl",
    rich_markup_mode="rich",
    add_completion=False,
    help="""
    A collection of handy tools for operators of [bold]charmed[/bold] kubeflow environments
    """,
)

console = Console()

epilog_check = '''
To view your juju installation's bundle, run,\n
$ ckfctl check -s local\n
To view a local bundle file, run\n
$ ckfctl check -s filename.yaml\n
You can use an extracted bundle from juju as well, with\n
$ juju export-bundle -o filename.yaml\n
\n
To view a bundle from the kubeflow git repo, just specify the channel \n
$ ckfctl check -s 1.7/stable\n
\n
Use the source and destination flags to compare 2 bundles for upgrades.\n
$ ckfctl check -s local -d 1.8/stable\n
$ ckfctl check -s localbundle.yaml -d 1.7/edge\n
$ ckfctl check -s local -d self\n
$ ckfctl check -s 1.7/edge -d latest/stable\n
$ ckfctl check -s 1.8/stable -d localbundle.yaml
'''
@cli.command(epilog=epilog_check)
def check(
    src: Annotated[
        str,
        typer.Option(
            "-s",
            "--src",
            help='''
            Version of kubeflow bundle, filename or special keyword, ex: 1.8/stable, local-bundle.yaml or local
            ''',
            rich_help_panel="Comparison tools",
            show_default=False,
        ),
    ] = None,
    dst: Annotated[
        str,
        typer.Option(
            "-d",
            "--dst",
            help='''
            Version of kubeflow bundle, filename or special keyword, ex: 1.8/stable, local-bundle.yaml, local or self\n
            special keyword "self" is used to infer and use the version of the source bundle\n
            special keyword "local" is used to get the bundle from the current juju client
            ''',
            rich_help_panel="Comparison tools",
            show_default=False,
        ),
    ] = None,
    formatting: Annotated[
        str,
        typer.Option(
            "-f",
            "--format",
            help="Output format, can be [bold]yaml[/bold], [bold]json[/bold] or table",
            rich_help_panel="Other Options",
        ),
    ] = "table",
    output: Annotated[
        str,
        typer.Option(
            "-o",
            "--output",
            help="File to store output",
            rich_help_panel="Other Options",
            show_default=False,
        ),
    ] = None,
):
    """
    :sparkles: [bold]View[/bold] kubeflow bundles or compare 2 bundles for possible upgrades
    """
    obj = {
        "src": src,
        "dst": dst,
        "format": formatting,
        "output_file": output,
    }

    ckupObj = CharmedKubeflowUpgradePlanner(**obj)
    ckupObj.main()


@cli.command(
    epilog="Either attemp a local scan, provide an image or a file of image names"
)
def scan(image, file, formatting, output, watch):
    """
    :mag_right: Use Trivvy to [bold]scan[/bold] pod images against aquasec's CVE database
    """
    pass


@cli.command()
def upgrade():
    """
    :collision: [bold]Upgrade[/bold] your juju installation of kubeflow to the specified target version
    """
    pass


@cli.command()
def deploy(
    mk8s: Annotated[
        str,
        typer.Option(
            "-m",
            "--mk8s",
            help="Version of microk8s snap to use, ex: 1.27/stable",
            rich_help_panel="Components",
        ),
    ] = "1.26/stable",
    kf: Annotated[
        str,
        typer.Option(
            "-k",
            "--kf",
            help="Version of kubeflow bundle to deploy, ex: 1.8/stable",
            rich_help_panel="Components",
        ),
    ] = "1.8/stable",
    skip_mk8s: Annotated[
        bool,
        typer.Option(
            "-s",
            "--skip-mk8s",
            help="Skip microk8s setup to make use of existing mk8s",
            rich_help_panel="Components",
        ),
    ] = False,
):
    """
    :rocket: [bold]Deploy[/bold] kubeflow using juju bootstrapped to microk8s
    """
    if mk8s:
        console.print(f"Deploying microk8s {mk8s} with kubeflow {kf} with juju 3.1...")
    else:
        console.print(f"Using current kubectl context to deploy kubeflow {kf} with juju 3.1...")

@cli.command()
def plugin(
    enable: Annotated[
        str,
        typer.Option(
            "-e",
            "--enable",
            help="Enable a supported plugin",
            show_default=False,
        ),
    ] = None,
    list: Annotated[
        str,
        typer.Option(
            "-l",
            "--list",
            help="List current supported plugins",
            show_default=False,
        ),
    ] = None,
):
    """
    :hammer: [bold]Enable[/bold] plugins such as observability or mlflow
    """
    pass


@cli.command()
def init():
    """
    :page_facing_up: Output a bash script to [bold]Prepare[/bold] your current node for ckf installation
    """
    console.print(Syntax(prepare_node_script(), "bash"), soft_wrap=True)


@cli.command(name="show-env-proxies")
def show_env_proxies():
    """
    :warning: Output a bash script to [bold]Prepare[/bold] your current node for ckf installation
    """
    console.print(get_env_proxy_vars())

def entrypoint() -> None:
    cli()

if __name__ == "__main__":
    entrypoint()
