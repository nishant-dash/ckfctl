import yaml
import json
from subprocess import run, PIPE, DEVNULL

JUJU="juju"

def juju_export_bundle(
    controller: str="microk8s-localhost",
    model: str="kubeflow",
    user: str="admin",
):
    cmd = [JUJU, "export-bundle", "-m", model] # f"{controller}:{user}/{model}",
    output = run(cmd, stdout=PIPE, stderr=DEVNULL, text=True).stdout
    output_yaml = None
    try:
        output_yaml = yaml.safe_load(output)
    except yaml.YAMLError as error:
        print(error)

    return output_yaml


def juju_info(application: str=None, formatting: str="json"):
    cmd = [JUJU, "info", application, "--format", formatting]
    output = run(cmd, stdout=PIPE, stderr=DEVNULL, text=True).stdout
    output_formatted = None
    try:
        if formatting == "json":
            output_formatted = json.loads(output)
        elif formatting == "yaml":
            output_formatted = yaml.safe_load(output)
        else:
            print("Unsupported format")
    except json.JSONDecodeError as error:
        print(error)
    except yaml.YAMLError as error:
        print(error)

    return output_formatted
