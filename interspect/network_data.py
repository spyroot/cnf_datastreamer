# Network os data collector.
# Mus
import subprocess
import warnings
from pathlib import Path
from typing import List


def run_distro_installer(inst_tool, apps: List[str]):
    """Install list of packages.
    :param inst_tool: path to a tool /bin/apt etc.
    :param apps: list of apps. ["netcat", "x"]
    :return:
    """
    if apps is None or len(apps) == 0:
        warnings.warn("Nothing to install")
        return

    if 'apt' in inst_tool:
        cmd_args = [inst_tool, "install", "-y"] + apps
    elif 'dnf' in inst_tool:
        cmd_args = [inst_tool, "install", "-y"] + apps
    elif 'packman' in inst_tool:
        cmd_args = [inst_tool, "-S", "-y"] + apps
    elif 'yum' in inst_tool:
        cmd_args = [inst_tool, "install", "-y"] + apps
    else:
        print("Unknown installer.")
        exit(1)

    cmdr = subprocess.run(cmd_args, check=True, capture_output=True)
    if cmdr.returncode != 0:
        print(f"Failed execute. {cmd_args}")
        return False

    return True


def installed(distro_installers=None):
    """
    :param distro_installers:
    :return:
    """
    if distro_installers is None:
        distro_installers = ["/bin/apt",
                             "/usr/bin/yum",
                             "/usr/bin/dnf",
                             "/usr/bin/zypper"
                             "/usr/bin/pacman"
                             ]

    return [(Path(p).exists(), p) for p in distro_installers]


def network_time_hw_offload_data(eth_name: str) -> dict:
    """Network adapter time offload capability
    :param eth_name: adapter name eth0 etc.
    :return: dict
    """
    cmdr = subprocess.run(["ethtool", "-T", eth_name], check=True, capture_output=True)
    decoded = cmdr.stdout.decode().split("\n")[:-1]
    return dict([s.strip().split(":", 1) for s in decoded if len(s) > 0])


def network_adapter_data(eth_name: str) -> dict:
    """Network adapter base data firmware/driver etc.
    :param eth_name: adapter name eth0 etc.
    :return: serialize data as dict
    """
    cmdr = subprocess.run(["ethtool", "-i", eth_name], check=True, capture_output=True)
    decoded = cmdr.stdout.decode().split("\n")[:-1]
    return dict([s.strip().split(":", 1) for s in decoded if len(s) > 0])


def network_addr_mac(eth_name: str) -> str:
    """Return network adapter permanent mac address.
    :param eth_name: name eth0 enp7s0 etc.
    :return:
    """
    cmdr = subprocess.run(["ethtool", "-P", eth_name], check=True, capture_output=True)
    output = cmdr.stdout.decode()
    if len(output) > 0 and cmdr.returncode == 0:
        return output.split("address:")[1:][0].strip()


def network_adapters_data(cmd):
    """
    :return:
    """
    try:
        result = subprocess.run(["lshw", "-class", "network", "-businfo"],
                                check=True, capture_output=True)

        if result.returncode != 0:
            print("Failed execute lshw, make sure it installed.")

        network_adapters = {}
        decoded = result.stdout.decode()
        if len(decoded) == 0:
            return {}
        decoded = decoded.split()

        for i in range(0, len(decoded)):
            network_adapter = {}
            if 'pci@' not in decoded[i]:
                continue
            network_adapter['pci'] = decoded[i].split("@")[1:][0]
            if decoded[i + 1] == 'network':
                continue
            eth_name = decoded[i + 1].strip()
            # skip all dev that has no device name , i.e virtual
            if eth_name is None or len(eth_name) == 0:
                warnings.warn(f"Skipping device {network_adapter['pci']}")
                continue

            network_adapter["name"] = eth_name
            network_adapter['address'] = network_addr_mac(eth_name)
            network_adapter.update(network_adapter_data(eth_name))
            network_adapter.update(network_time_hw_offload_data(eth_name))
            network_adapters[eth_name] = network_adapter

        return network_adapters
    except FileNotFoundError as fnfe:
        print("You need to install lshw and ethtool first.")

