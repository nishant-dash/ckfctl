JUJU_CHANNEL = "3.1/stable"
SUPPORTED_RELEASE = "jammy"
PREPARE_NODE_TEMPLATE = f"""#!/bin/bash

[ $(lsb_release -sc) != '{SUPPORTED_RELEASE}' ] && \
{{ echo 'ERROR: Charmed Kubeflow deploy is only supported on {SUPPORTED_RELEASE}'; exit 1; }}

# :warning: Node Preparation for Charmed Kubeflow :warning:
# All of these commands perform privileged operations
# please review carefully before execution.
USER=$(whoami)

if [ $(id -u) -eq 0 -o "$USER" = root ]; then
    echo " ERROR: Node Preparation script for ckfctl must be executed by \
    non-root user with sudo permissions."
    exit 1
fi

# Check if user has passwordless sudo permissions and setup if need be
SUDO_ASKPASS=/bin/false sudo -A whoami &> /dev/null &&
sudo grep -r $USER /etc/{{sudoers,sudoers.d}} | grep NOPASSWD:ALL &> /dev/null || {{
    echo "$USER ALL=(ALL) NOPASSWD:ALL" > /tmp/90-$USER-sudo-access
    sudo install -m 440 /tmp/90-$USER-sudo-access /etc/sudoers.d/90-$USER-sudo-access
    rm -f /tmp/90-$USER-sudo-access
}}

# Ensure OpenSSH server is installed
dpkg -s openssh-server &> /dev/null || {{
    sudo apt install -y openssh-server
}}

# Increase the number of inotify watchers per user
echo "fs.inotify.max_user_instances = 1024" | sudo tee /etc/sysctl.d/80-ckfctl.conf
echo "fs.inotify.max_user_watches = 655360" | sudo tee -a /etc/sysctl.d/80-ckfctl.conf
sudo sysctl -q -p /etc/sysctl.d/80-ckfctl.conf

# Make snap connections
# to talk to juju 3 client
sudo snap connect ckfctl:juju-bin juju
# to use juju ssh keys
sudo snap connect ckfctl:ssh-public-keys
# to read juju client configs
sudo snap connect ckfctl:dot-local-share-juju
# to write and modify juju client configs
sudo snap connect ckfctl:juju-client-observe

# Add $USER to the snap_daemon group and adopt new permissions
sudo addgroup $USER snap_daemon
newgrp snap_daemon

# Generate keypair and set-up prompt-less access to local machine
[ -f $HOME/.ssh/id_rsa ] || ssh-keygen -b 4096 -f $HOME/.ssh/id_rsa -t rsa -N ""
cat $HOME/.ssh/id_rsa.pub >> $HOME/.ssh/authorized_keys
ssh-keyscan -H $(hostname --all-ip-addresses) >> $HOME/.ssh/known_hosts

# Install the Juju snap
sudo snap install --channel {JUJU_CHANNEL} juju

# Workaround a bug between snapd and juju
mkdir -p $HOME/.local/share
mkdir -p $HOME/.kube

# Install misc. helpers
sudo snap install juju-wait --classic
"""

def prepare_node_script() -> str:
    """Generate script to prepare a node for ckfctl use."""
    return PREPARE_NODE_TEMPLATE
