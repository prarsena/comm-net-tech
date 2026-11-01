#!/usr/bin/env python3
import argparse
import ipaddress
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class NetworkInfo:
    interface: str
    address: ipaddress.IPv4Address
    network: ipaddress.IPv4Network
    netmask: ipaddress.IPv4Address
    broadcast: Optional[ipaddress.IPv4Address]


def run_command(arguments: list[str]) -> str:
    try:
        result = subprocess.run(
            arguments,
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError as error:
        raise RuntimeError(f"Required system command not found: {arguments[0]}") from error
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or "command failed"
        raise RuntimeError(f"{' '.join(arguments)}: {detail}") from error
    return result.stdout


def default_interface() -> str:
    system = platform.system()
    if system == "Darwin":
        output = run_command(["route", "-n", "get", "default"])
        match = re.search(r"^\s*interface:\s*(\S+)", output, re.MULTILINE)
    elif system == "Linux":
        output = run_command(["ip", "-4", "route", "show", "default"])
        match = re.search(r"(?:^|\s)dev\s+(\S+)", output, re.MULTILINE)
    else:
        raise RuntimeError(
            f"Automatic interface discovery is not supported on {system}; "
            "specify --interface."
        )

    if match is None:
        raise RuntimeError("Could not find a default-route interface; specify --interface.")
    return match.group(1)


def network_from_address(
    interface: str,
    address_text: str,
    prefix_length: int,
    reported_broadcast: Optional[str],
) -> NetworkInfo:
    address = ipaddress.IPv4Address(address_text)
    network_interface = ipaddress.IPv4Interface(f"{address}/{prefix_length}")
    network = network_interface.network
    netmask = network.netmask

    broadcast = None
    if (
        prefix_length <= 30
        and reported_broadcast is not None
        and ipaddress.IPv4Address(reported_broadcast) == network.broadcast_address
    ):
        broadcast = network.broadcast_address

    return NetworkInfo(interface, address, network, netmask, broadcast)


def mac_network_info(interface: str) -> NetworkInfo:
    output = run_command(["ifconfig", interface])
    pattern = re.compile(
        r"\binet\s+([0-9.]+)\s+netmask\s+(0x[0-9a-fA-F]+|[0-9.]+)"
        r"(?:\s+broadcast\s+([0-9.]+))?"
    )

    for match in pattern.finditer(output):
        address_text, mask_text, broadcast_text = match.groups()
        if mask_text.lower().startswith("0x"):
            netmask = ipaddress.IPv4Address(int(mask_text, 16))
        else:
            netmask = ipaddress.IPv4Address(mask_text)
        prefix_length = ipaddress.IPv4Network(f"0.0.0.0/{netmask}").prefixlen
        return network_from_address(
            interface,
            address_text,
            prefix_length,
            broadcast_text,
        )

    raise RuntimeError(f"No IPv4 address was found on interface {interface}.")


def linux_network_info(interface: str) -> NetworkInfo:
    output = run_command(["ip", "-o", "-4", "addr", "show", "dev", interface])
    match = re.search(
        r"\binet\s+([0-9.]+)/(\d+)(?:\s+brd\s+([0-9.]+))?",
        output,
    )
    if match is None:
        raise RuntimeError(f"No IPv4 address was found on interface {interface}.")

    address_text, prefix_text, broadcast_text = match.groups()
    return network_from_address(
        interface,
        address_text,
        int(prefix_text),
        broadcast_text,
    )


def get_network_info(interface: Optional[str]) -> NetworkInfo:
    selected_interface = interface or default_interface()
    system = platform.system()
    if system == "Darwin":
        return mac_network_info(selected_interface)
    if system == "Linux":
        return linux_network_info(selected_interface)
    raise RuntimeError(f"Network information is not supported on {system}.")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Show the IPv4 network information for an interface."
    )
    parser.add_argument(
        "--interface",
        help="interface to inspect; defaults to the system's default-route interface",
    )
    parser.add_argument(
        "--broadcast-only",
        action="store_true",
        help="print only the broadcast address (for use by the sender script)",
    )
    arguments = parser.parse_args()

    try:
        info = get_network_info(arguments.interface)
    except (OSError, RuntimeError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1

    if arguments.broadcast_only:
        if info.broadcast is None:
            print(
                "Error: this interface does not report a usable IPv4 broadcast address.",
                file=sys.stderr,
            )
            return 1
        print(info.broadcast)
        return 0

    broadcast = str(info.broadcast) if info.broadcast is not None else "unavailable"
    rows = (
        ("Interface:", info.interface),
        ("Host IPv4:", str(info.address)),
        ("Network address:", str(info.network.network_address)),
        ("Broadcast address:", broadcast),
        ("Network mask:", str(info.netmask)),
        ("CIDR:", str(info.network)),
    )
    label_width = max(len(label) for label, _ in rows)
    for label, value in rows:
        print(f"{label:<{label_width}} {value}")

    if info.broadcast is None:
        print("This interface cannot be used for the broadcast send demo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
