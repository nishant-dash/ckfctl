from ckfctl.kf_upgrade_planner import kup
from ckfctl.kf_image_scanner import kvs
from ckfctl.juju_helper import juju_export_bundle
import typer
from typing_extensions import Annotated
from typing import List

cli = typer.Typer(
    name="ckfctl",
    rich_markup_mode="rich",
    add_completion=False,
    help="""
    A collection of handy tools for operators of [bold]charmed[/bold] kubeflow environments
    """,
)

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
            print("When checking for upgrade choose one of:")
            print("- Two local bundles")
            print("- One local One remote bundle")
            raise typer.Exit(code=1)

        obj["file"] = file[0]
        if len(file) == 2:
            obj["target_version"] = -1
            obj["second_file"] = file[1]
        elif len(file) > 2:
            print("Too many files!")
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
        print(f"Inferring input bundle's version for target version as: {kupObj.target_version}")

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
# @typer.Option(
#     "-i",
#     "--image",
#     help="name of a container image",
#     metavar="<image_name>",
# )
# @typer.Option(
#     "-f",
#     "--file",
#     help="file containing a list of container image names",
#     metavar="<file>",
# )
# @typer.Option(
#     "--format",
#     "formatting",
#     help="Output format, can be yaml, json or table",
#     type=typer.Choice(["yaml", "json"]),
# )
# @typer.Option(
#     "-o",
#     "--output",
#     help="File to store output",
#     metavar="<output_file>",
# )
# @typer.Option(
#     "-w",
#     "--watch",
#     help="Watch as scan results for each come in one by one",
#     show_default=True,
#     default=False,
#     is_flag=True,
# )
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
def init():
    """
    :rocket: [bold]Deploy[/bold] kubeflow using juju bootstrapped to microk8s
    """
    pass

@cli.command()
def plugins():
    """
    :hammer: [bold]Enable[/bold] plugins such as observability or mlflow
    """
    pass

def entrypoint() -> None:
    cli()

if __name__ == "__main__":
    entrypoint()
