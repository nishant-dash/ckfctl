'''
Tool to parse current deployment bundle, extrapolate possible kubeflow version and 
print rudimentary upgrade info
'''

import yaml
import json

# procs
import requests
import subprocess as sp

# formatting stuff
from rich.console import Console
from rich.table import Table
from rich.progress import track
from rich import box

# misc
from os.path import isfile, exists
from ckfctl.juju_helper import juju_export_bundle

# global declarations
console = Console()
HTTP_OK = 200
TRACKS = ["stable", "edge", "beta"]
ARG_SPECIAL_TYPES = {
    "src": ["local"],
    "dst": ["local", "self"],
}
ARG_TYPES = {
    "src": ["local", "file", "channel"],
    "dst": ["local", "self", "file", "channel"],
}

class CharmedKubeflowUpgradePlanner:
    def __init__(self, **kwargs):
        self.kf_source = "https://github.com/canonical/bundle-kubeflow"
        self.upgrade_docs = "https://charmed-kubeflow.io/docs/upgrade"
        self.anchor_app = "kubeflow-dashboard"
        self.index = {"beta": 0, "stable": 1, "edge": 2}
        self.juju = "juju"
        self.output_formats = ["yaml", "json", "table"]
        self.source_version = None
        for k,v in kwargs.items():
            setattr(self, k, v)


    def _print(self, output, columns=None) -> None:
        """
        Helper to either print to terminal or write to a file

        Returns:
        - None
        """
        if not self.output_file:
            if self.format == "table":
                table = Table(box=box.ROUNDED)
                for c in columns:
                    table.add_column(c)
                for r in output:
                    table.add_row(*r)
                console.print(table)
            else:
                console.print(output)
        else:
            # check validity of file
            if '/' in self.output_file:
                path = self.output_file.split('/')
                path = "/".join(path[:-1])
                if not exists(self.output_file):
                    console.print(f"Invalid path {path}")
                    return None
            with open(self.output_file, 'w') as f:
                f.write(output)


    def color_me(self, string: str, color: str="green") -> str:
        """
        Embed rich coloring scheme into strings

        Returns:
        - color embedded string
        """
        if not self.output_file:
            return f"[{color}]{string}[/{color}]" 
        return string


    def pprint(self, d, upgrades=False) -> None:
        """
        Pretty print a bundle either in tby itself or in the context of upgrades

        Returns:
        - None
        """
        if self.format == "yaml":
            self._print(yaml.dump(d))
        elif self.format == "json":
            self._print(json.dumps(d))
        else:
            temp = []
            if upgrades:
                fields = ["Charm", "Src Channel", "S", "Dst Channel", "Src Rev", "S", "Dst Rev"]
                for k,v in d.items():
                    if v["channel_upgrade"] == "->":
                        temp.append([self.color_me(k)] + [self.color_me(str(v2)) for v2 in v.values()])
                    elif v["revision_upgrade"] == "->":
                        temp.append([self.color_me(k)])
                        for k2, v2 in v.items():
                            if "revision" in k2:
                                temp[-1].extend([self.color_me(str(v2))])
                            else:
                                temp[-1].extend([str(v2)])
                    else:
                        temp.append([k] + [str(v2) for v2 in v.values()])
            else:
                fields = ["Charm", "Channel", "Revision"]
                for k,v in d.items():
                    temp2 = [k]
                    for k2, v2 in v.items():
                        if k2 != "charm_name":
                            temp2.extend([str(v2)])
                    temp.append(temp2)
            self._print(temp, columns=fields)


    def transform(self, bundle, get_revision=False) -> {}:
        """
        Transform the juju bundle yaml to a dict that maps
        charm name -> {channel, revision}

        Returns:
        - Dictionary of charm name -> {channel, revision}
        """
        if not bundle:
            return None, None

        charm_version_dict = {}
        if not get_revision:
            for charm, info in bundle["applications"].items():
                rev = "0"
                if "revision" in info:
                    rev = info["revision"]
                if "local" in info["charm"]:
                    charm_version_dict[charm] = {"channel": "local", "revision": rev}
                else:
                    charm_version_dict[charm] = {"channel": info["channel"], "revision": rev}
        else:
            for charm, info in bundle["applications"].items():
                charm_version_dict[charm] = {"channel": info["channel"], "charm_name": info["charm"]}
            self.get_revision_numbers(charm_version_dict)

        return charm_version_dict , charm_version_dict[self.anchor_app]["channel"]


    def compare_channels(a :str, b :str) -> None:
        """
        @TODO Create a channel object, with functions 
        - to help identify a string as a channel
        - to compare two channels
        """
        pass


    def check_downgrade(self, source, target) -> bool:
        """
        @TODO Hacky function to check downgrade

        Returns:
        - None
        """
        src = source[self.anchor_app]
        dst = target[self.anchor_app]
        src_channel, src_mode = src["channel"].split("/")
        dst_channel, dst_mode = dst["channel"].split("/")

        # if dst_channel == "latest":
        #     if src_channel == "latest":
        #         if self.index[dst_mode] < self.index[src_mode]:
        #             print("Downgrade detected!")
        #             return True
        if float(dst_channel) < float(src_channel):
            console.print("Downgrade detected!")
            return True
        elif dst_channel == src_channel:
            if self.index[dst_mode] < self.index[src_mode]:
                console.print("Downgrade detected!")
                return True
        elif int(dst["revision"]) < int(src["revision"]):
            console.print("Downgrade detected!")
            return True
        return False


    def upgrade_flagger(self, source, target) -> None:
        """
        @TODO An unsightly function in despearate need of simplification and elegance
        Print a bespoke diff of the bundles (dicts) in a manner that flags charms for upgrades

        Returns:
        - None
        """
        final_dict = {}
        num_changes = 0

        final_view = {}
        for charm, info in target.items():
            final_view[charm] = {"src": None, "dst": None}
            final_view[charm]["dst"] = info
            if charm in source:
                if charm not in final_view:
                    final_view[charm] = {"src": None, "dst": None}
                final_view[charm]["src"] = source[charm]

        for charm, view in final_view.items():
            final_dict[charm] = {
                "src_channel": None, "channel_upgrade" : "=","dst_channel": None,
                "src_revision": None, "revision_upgrade" : "=", "dst_revision": None,
            }
            if view["src"]: 
                final_dict[charm]["src_channel"] = view["src"]["channel"]
                final_dict[charm]["src_revision"] = int(view["src"]["revision"])
            if view["dst"]: 
                final_dict[charm]["dst_channel"] = view["dst"]["channel"]
                final_dict[charm]["dst_revision"] = int(view["dst"]["revision"])
            
            if final_dict[charm]["src_channel"] and final_dict[charm]["dst_channel"]:
                if final_dict[charm]["dst_channel"] != final_dict[charm]["src_channel"]:
                    final_dict[charm]["channel_upgrade"] = "->"
            if final_dict[charm]["src_revision"] and final_dict[charm]["dst_revision"]:
                if final_dict[charm]["dst_revision"] > final_dict[charm]["src_revision"]:
                    final_dict[charm]["revision_upgrade"] = "->"

            if final_dict[charm]["channel_upgrade"] or final_dict[charm]["revision_upgrade"]:
                num_changes += 1
            if not final_dict[charm]["src_channel"] and final_dict[charm]["dst_channel"]:
                final_dict[charm]["channel_upgrade"] = "+"
                final_dict[charm]["revision_upgrade"] = "+"

        self.pprint(final_dict, upgrades=True)
        console.print(f"\n{num_changes} charms need upgrades!")

        apps_to_remove = []
        for app in source.keys():
            if app not in target:
                apps_to_remove.append(app)
        if len(apps_to_remove) > 0:
            console.print(f"{len(apps_to_remove)} charms not found in target bundle: {apps_to_remove}")

        self.check_downgrade(source, target)
        console.print(f"Also check upgrade docs at {self.upgrade_docs} for any relevant steps and caveats!")


    def get_revision_numbers(self, bundle) -> {}:
        """
        Query charmhub using the juju client to get revision numbers for charms

        Returns:
        - A transformed version of the input bundle, 
        but with revision number info embeded into the dictionary as well
        """
        # Currently, the charmed kf bundle in the git repo does not include 
        # information about revision numbers, only channels.
        console.print("Getting revision numbers from charmhub via local juju client...")
        # for each charm, check with juju info to see what revision you get
        for charm, info in track(bundle.items(), description="Processing..."):
            # get the juju info as json
            cmd = [self.juju, "info", info["charm_name"], "--format", "json"]
            output = sp.run(cmd, stdout=sp.PIPE, stderr=sp.DEVNULL)
            # parse json for what we need
            juju_info = ""
            try:
                juju_info = json.loads(output.stdout)
            except json.JSONDecodeError as error:
                console.print(error)
            channels = juju_info["channels"]
            cur_channel = info["channel"].split('/')[0]
            cur_track = info["channel"].split('/')[1]
            if cur_channel not in channels:
                bundle[charm]["revision"] = "Error"
            else:    
                bundle[charm]["revision"] = channels[cur_channel][cur_track][0]["revision"]


    def download_bundle(self, channel_string :str = None) -> {}:
        """
        Given a channel, download the bundle yaml from Charmed Kubeflow's github
        and return the yaml as a dictionary

        Returns:
        - Dictionary format of the remote yaml file
        """
        if not channel_string:
            # console.print("Unable to get version")
            return None
        target_bundle = None
        version, channel = channel_string.split("/")
        if version == "latest":
            url = f"{self.kf_source}/raw/main/releases/{version}/{channel}/bundle.yaml"
        else:
            url = f"{self.kf_source}/raw/main/releases/{version}/{channel}/kubeflow/bundle.yaml"
        response = requests.get(url)
        console.print (f"Downloading kf {channel_string} bundle...")
        if response.status_code != HTTP_OK:
            response.raise_for_status()
            console.print_exception(f"Target bundle for Kubeflow {channel_string} not found!")
        else:
            try:
                target_bundle = yaml.safe_load(response.content)
            except yaml.YAMLError as error:
                console.print(error)

        return target_bundle


    def load_bundle(self, bundle_file) -> {}:
        """
        Given a filesystem filename, yaml load it

        Returns:
        - Dictionary format of the yaml file
        """
        bundle = None
        with open(bundle_file, "r") as f:
            try:
                bundle = yaml.safe_load(f)
            except yaml.YAMLError as error:
                console.print(error)
        return bundle


    def is_floating_numeric(self, string: str) -> bool:
        """
        Given a string check if its in the form of a float number

        Returns:
        - True/False
        """
        try:
            float(string)
            return True
        except ValueError as error:
            console.print_exception(error)
            return False

    def is_channel_format(self, string: str) -> bool:
        """
        Given a string check if its in the form of a channel string
        For ex: 1.8/stable, 1.45/beta, 3.1/edge

        Returns:
        - True/False
        """
        if '/' in string:
            channel = string.split('/')[0]
            track = string.split('/')[1]
            if track in TRACKS:
                if channel == "latest" or self.is_floating_numeric(channel):
                    return True
        return False

    def infer_type(self, arg, mode) -> str:
        """
        Given a argument such as filename, special keyword or channel like 1.8/stable
        infer its type as such

        Returns:
        - A string that denotes the type of argument such as file, channel(ex: 1.8/stable)
        or some special keywords
        """
        inferred_type = None
        if arg in ARG_SPECIAL_TYPES[mode]:
            inferred_type = arg
        elif isfile(arg):
            inferred_type = "file"
        elif self.is_channel_format(arg):
            inferred_type = "channel"

        # console.print(f"Inferred type of {arg} is {inferred_type}")
        return inferred_type

    def get_data(self, arg, arg_type) -> ({}, str):
        """
        Given a argument such as filename, special keyword or channel like 1.8/stable
        Use the argument and its type to call the appropriate function

        Returns:
        - A dictionary map charm names to a dictionary of charm channel and revisions
        - The version of the bundle w.r.t kubeflow
        """
        data = {}
        version = None
        bundle = None        
        match arg_type:
            case "local":
                bundle = juju_export_bundle()
            case "self":
                console.print(f"Detected version of source bundle as {self.source_version}")
                bundle = self.download_bundle(self.source_version)
            case "file":
                bundle = self.load_bundle(arg)
            case "channel":
                bundle = self.download_bundle(arg)
            case _:
                console.print(f"Unknow type {arg_type}!")
                bundle = None

        if arg_type in ["channel", "self"]:
            data, version = self.transform(bundle, get_revision=True)
        else:
            data, version = self.transform(bundle)

        return data, version

    def main(self):
        """
        Main logic of the upgrade flagger
        """
        src_type = None
        src_data = None
        if self.src:
            src_type = self.infer_type(self.src, mode="src")
            src_data, self.source_version = self.get_data(self.src, src_type)

        dst_type = None
        dst_data = None
        if self.dst:
            dst_type = self.infer_type(self.dst, mode="dst")
            dst_data, _ = self.get_data(self.dst, dst_type)
        
        if src_data:
            if dst_data:
                self.upgrade_flagger(source=src_data, target=dst_data)
            else:
                self.pprint(src_data)
        else:
            if dst_data:
                self.pprint(dst_data)
