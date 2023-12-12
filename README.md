
# ckfctl (Charmed-KubeFlow-ConTroL)
### A collection of handy wrapper tools for operators of kubeflow environments


With kf-tools you have access to a few command line tools to help you operate your kubeflow deployment. These include:


1) `ckfctl check` (Kube Upgrade Planner)
A tool to help you view your juju based kubeflow bundle, in terms of the charm, channel and revision. You can compare 2 local bundles or compare a local with a remote charmed kubeflow bundle and view the differences between these bundles based off their versioning information.

2) Other commands are WIP...


## Installation

### Install from source

```bash
git clone https://github.com/nishant-dash/ckfctl
cd ckfctl/ && pip install --no-build -e .
ckfctl --help
```

### Install from snap (WIP)

```bash
sudo snap install ckfctl
```

However, after the snap install, you need to make some connectiong to give ckfctl access
to certain resources
```bash
# to talk to juju 3 client
sudo snap connect ckfctl:juju-bin juju
# to use juju ssh keys
sudo snap connect ckfctl:ssh-public-keys
# to read juju client confis
sudo snap connect ckfctl:dot-local-share-juju
# to write and modify juju client configs
sudo snap connect ckfctl:juju-client-observe
```

## Building

### Build snap

```bash
make build
```

### Use the locally built snap
```bash
sudo snap install ckfctl.snap --dangerous
# you will need to run the snap connect lines above ^ if this is the first time
```

## Usage

You can view all subcommands and flags with `-h` or `--help`.

<br> ![screenshot](/png/screenshot-help.png)


### ckfctl check (Kube Upgrade and Bundle Info Viewer)

```bash
# run against local environment, this will run juju commands
ckfctl check -s local

# view a local bundle
ckfctl check -s my-kf-bundle.yaml

# view a remote bundle
ckfctl check -s 1.8/stable

# compare a local and remote bundle
ckfctl check -s my-kf-bundle.yaml -d 1.7/stable

# compare local environment to a remote channel
ckfctl check -s local -d 1.8/edge

# compare local environment to its own latest version
ckfctl check -s local -d self
```

## Version Info/Dependencies

- juju 3 client
