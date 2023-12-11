from rich.console import Console
from juju_helper import juju_deploy, juju_run, juju_bootstrap, juju_add_model, juju_ssh
import yaml

console = Console()
JUJU_AGENT_VERSION="3.1.6"
MANUAL_CLOUD_CONTROLLER="manual"
MK8S_CLOUD_CONTROLLER="microk8s-localhost"
KUBE_CONFIG="~/.kube/config"

def _deploy_mk8s_snap(channel: str):
    pass

def _deploy_manual_localhost():
    user = get_user()
    ip = get_local_ip()
    juju_bootstrap(
        version=JUJU_AGENT_VERSION,
        cloud=f"manual/{user}@{ip}"
    )

def _deploy_mk8s_charm(channel: str):
    """
    juju bootstrap --agent-version=3.1.6 manual/ubuntu@$(hostname -i)
    juju switch manual:admin/controller
    juju deploy microk8s --channel=channel --to 0
    """
    _deploy_manual_localhost()
    juju_deploy(
        app="microk8s",
        channel=channel,
        to="0",
        controller=MANUAL_CLOUD_CONTROLLER,
        model="controller"
    )
    # save creds
    # connect to microk8s strict content slot?
    kube_config = juju_ssh(
        controller=MANUAL_CLOUD_CONTROLLER,
        model="controller",
        app="microk8s",
        command="microk8s config"
    )
    try:
        with open(KUBE_CONFIG, 'w') as f:
            yaml.dump(yaml.safe_load(kube_config), f)
    except yaml.YAMLError as error:
        console.print(error)
    # except IOError as error:
    #     console.print(error)


def deploy_microk8s(channel: str, mode: str="snap"):
    if mode == "snap":
        _deploy_mk8s_snap(channel)
    elif mode == "charm":
        _deploy_mk8s_charm(channel)
    else:
        console.print(f"{mode} unknown")
    return

def deploy_kubeflow(channel: str):
    """
    juju add-k8s mk8s --client
    juju bootstrap mk8s --agent-version=JUJU_AGENT_VERSION
    """
    juju_bootstrap(version=JUJU_AGENT_VERSION, cloud="mk8s")
    juju_add_model("kubeflow")
    juju_deploy(
        app="kubeflow",
        channel=channel,
        controller=MK8S_CLOUD_CONTROLLER,
        model="kubeflow")
    pass


def main():
    deploy_microk8s(channel="1.28/stable", mode="charm")
    deploy_kubeflow(channel="1.8/stable")
