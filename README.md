
# ckfctl (Charmed-KubeFlow-ConTroL)
### A collection of handy wrapper tools for operators of kubeflow environments


With kf-tools you have access to a few command line tools to help you operate your kubeflow deployment. These include:


1) ckfctl check (Kube Upgrade Planner)
A tool to help you view your juju based kubeflow bundle, in terms of the charm, channel and revision. You can compare 2 local bundles or compare a local with a remote charmed kubeflow bundle and view the differences between these bundles based off their versioning information.

3) ckfctl scan (Kube Vulnerability Scanner)
This scanner uses [trivy](https://github.com/aquasecurity/trivy) to help you scan your pod images against a databases of known vulnerabilities. It does not scan the container image itself, but for references of CVEs against the image.


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

## Usage

You can view all subcommands and flags with `-h` or `--help`.


### ckfctl check (Kube Upgrade and Bundle Info Viewer)

```bash
# run against local environment, this will run juju commands
ckfctl check -l

# view a local bundle
ckfctl check -f my-kf-bundle.yaml

# view a remote bundle
ckfctl check -t 1.7/stable

# compare a local and remote bundle
ckfctl check -f my-kf-bundle.yaml -t 1.7/stable

# compare two local bundles
ckfctl check -f my-kf-bundle.yaml -f my-kf-bundle2.yaml

# compare two local bundles and get a yaml/json output
ckfctl check -f my-kf-bundle.yaml -f my-kf-bundle2.yaml --format yaml -o output.yaml
```

### ckfctl scan (Kube Vulnerability Scanner)

```bash
# scan a particular container image
ckfctl scan -i <image_name>

# scan a files of image names 
ckfctl scan -f <file>

# generate a yaml/json report
ckfctl scan -f <file> --format json

# watch output as it scans
ckfctl scan -f <file> -w

# Not Out yet
# scan current local kubeflow installation that your juju controller has access to 
# and your kubectl command line tool is configured with
# this command is namespaced, with the default of kubeflow
ckfctl scan

# scan other namespace(s) or all namespaces (default is kubeflow)
ckfctl scan -n monitoring -s
ckfctl scan -n monitoring,custom,kubeflow -s
ckfctl scan --all-namespaces
```
