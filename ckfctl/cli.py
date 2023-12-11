# ckfctl.
from ckfctl.kf_upgrade_planner import kup
from ckfctl.kf_image_scanner import kvs
from ckfctl.juju_helper import juju_export_bundle
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
$ ckfctl check -l\n
To view a local bundle file, run\n
$ ckfctl check -f filename\n
You can extract a bundle from juju as well, with\n
$ juju export-bundle -o filename\n
\n
To view a bundle from the kubeflow git repo, run with only the "-t" flag\n
and then a channel after it. eg: ckfctl check -t 1.7/stable\n
\n
When more than one(maximum of 2) are provided, an automatic check\n
for upgrade is run.\n
$ ckfctl check -l -t 1.8/stable\n
$ ckfctl check -f localbundle.yaml -t 1.7/edge
'''
@cli.command(epilog=epilog_check)
def check(
    local: Annotated[
        bool,
        typer.Option(
            "-l",
            "--local",
            help="Check juju installation for Kubeflow",
        ),
    ] = False,
    file: Annotated[
        List[str],
        typer.Option(
            "-f",
            "--file",
            help='''
                Input juju kubeflow bundle yaml, can specify 2 local files\n
                using this same flag, treating first file as src for diff
            ''',
            show_default=False,
        ),
    ] = None,
    target: Annotated[
        str,
        typer.Option(
            "-t",
            "--target",
            help="Target version of kubeflow bundle, ex: 1.8/stable, 1.7/beta or self",
        ),
    ] = None,
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
        "local": local,
        "target_version": target,
        "file": None,
        "second_file": None,
        "format": formatting,
        "output_file": output,
    }

    if file:
        if len(file) == 2 and obj["target_version"]:
            console.print("When checking for upgrade choose one of:")
            console.print("- Two local bundles")
            console.print("- One local One remote bundle")
            raise typer.Exit(code=1)

        obj["file"] = file[0]
        if len(file) == 2:
            obj["target_version"] = -1
            obj["second_file"] = file[1]
        elif len(file) > 2:
            console.print("Too many files!")
            raise typer.Exit(code=1)


    kupObj = kup(**obj)

    if kupObj.local:
        local_bundle = juju_export_bundle()
        charm_version_dict, local_version = kupObj.transform(local_bundle)
        kupObj.pprint(charm_version_dict)
        raise typer.Exit(code=0)

    local_version = None
    if kupObj.file:
        # get local bundle
        local_bundle = kupObj.load_bundle(kupObj.file)
        charm_version_dict, local_version = kupObj.transform(local_bundle)
        if not kupObj.target_version:
            kupObj.pprint(charm_version_dict)
            raise typer.Exit(code=0)

    if kupObj.target_version == "self":
        kupObj.target_version = local_version
        console.print(f"Inferring input bundle's version for target version as: {kupObj.target_version}")

    if kupObj.target_version == -1:
        # get second local bundle file
        target_bundle = kupObj.load_bundle(kupObj.second_file)
        charm_version_dict_target, kupObj.target_version = kupObj.transform(target_bundle)
    else:
        # get target bundle
        target_bundle = kupObj.download_bundle()
        if not target_bundle:
            raise typer.Exit(code=1)
        charm_version_dict_target, kupObj.target_version = kupObj.transform(target_bundle, get_revision=True)
    if not kupObj.file:
        kupObj.pprint(charm_version_dict_target)
        raise typer.Exit(code=0)

    # print upgrade opportunities
    kupObj.upgrade_flagger(source=charm_version_dict, target=charm_version_dict_target)

@cli.command(
    epilog="Either attemp a local scan, provide an image or a file of image names"
)
def scan(image, file, formatting, output, watch):
    """
    :mag_right: Use Trivvy to [bold]scan[/bold] pod images against aquasec's CVE database
    """
    kvs_obj = kvs(formatting, output, watch)
    if image:
        kvs_obj.scan([image])
    if file:
        images_list = kvs_obj.load_file(file)
        if images_list:
            kvs_obj.scan(images_list)
    kvs_obj.print_report()


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
