# Chapter 5: UDP Broadcast Demo

This demo discovers an IPv4 interface's address, network, mask, CIDR, and broadcast
address, then sends one short UDP message to port **17429**. The receiver prints
messages in its terminal.

## Run the demo

Install `socat` if you use the Bash sender script or the macOS/Linux manual commands:

- macOS: `brew install socat`
- Debian/Ubuntu: `sudo apt install socat`

The examples use Python 3.9 or later. Interface discovery supports macOS and Linux;
Linux needs the `ip` command from iproute2.

## Start the listener

### macOS native app

Stop any other listener already using UDP/17429, then build the native app:

```bash
bash code/ch05/broadcaster/macos/build_app.sh
open code/ch05/broadcaster/macos/build/CS240BroadcastListener.app
```

The build script detects the machine architecture, including Apple Silicon when the
terminal is running under Rosetta. It builds x86_64 with a macOS 10.6 deployment target
on 64-bit Intel Macs, or arm64 with a macOS 11.0 deployment target on Apple Silicon.
On Intel, set `MACOSX_DEPLOYMENT_TARGET=10.10` before running the script if you prefer
the more conservative 10.10 baseline:

```bash
MACOSX_DEPLOYMENT_TARGET=10.10 bash code/ch05/broadcaster/macos/build_app.sh
```

The app uses AppKit and the system UDP socket APIs without ARC so it can build for
older Intel runtimes. The 10.6 target compiles with the installed SDK, but should also be
tested on Snow Leopard before being treated as certified support.
Each received datagram is appended as a new line in the scrollable message log, with
its sender address. The log stays in memory while the app runs and is discarded when
you quit; it is not written to disk. Closing the app's last window quits the app and
stops the listener. You can also choose **Quit** from the app menu or press Command-Q.
Messages are unauthenticated plain text; any host able to reach UDP/17429 can append
to the window, so this is a demonstration rather than secure messaging.

### Python alternative

On Linux or other hosts, the Python listener remains available:

```bash
python3 code/ch05/broadcaster/listener.py
```

On a host with Tkinter and a desktop session, it can also show the latest message in a
small Python window:

```bash
python3 code/ch05/broadcaster/listener.py --popup
```

The window updates in place rather than opening a new window for every datagram.
Close the window to stop the listener. Tkinter needs a desktop session; on some Linux
installations it must be installed separately (for example, `python3-tk`).

In terminal 2, inspect the default-route interface:

```bash
python3 code/ch05/broadcaster/network_info.py
```

If needed, choose an interface explicitly (for example, `en0` on many Macs):

```bash
python3 code/ch05/broadcaster/network_info.py --interface en0
```

Send a message:

```bash
bash code/ch05/broadcaster/send_broadcast.sh "Hello from CS240"
```

The sender prints the network details and asks for confirmation before sending.
To choose an interface, pass it after the message:

```bash
bash code/ch05/broadcaster/send_broadcast.sh "Hello from CS240" en0
```

The sender sends one datagram, limits it to 256 bytes, and does not retry. The listener
binds to UDP port 17429 on all local interfaces so it can receive the subnet broadcast.
Stop it with Ctrl-C.

### Send one datagram manually

These commands discover the broadcast address for the IPv4 default-route interface
without running `network_info.py`. They send immediately, without the sender script's
confirmation prompt or 256-byte check. Verify the selected interface and use only a
short test message on a network where you have permission.

#### tl;dr

Replace the Broadcast with the actual Broadcast IP of your network and run this one-liner:

```bash
export BROADCAST='192.168.8.255' && printf '%s' 'Hello from CS240' | socat -u - UDP4-DATAGRAM:$BROADCAST:17429,broadcast
```


#### macOS (Bash)

```bash
set -eu
IFACE="$(route -n get -inet default | awk '$1 == "interface:" { print $2; exit }')"
if [ -z "$IFACE" ]; then
    printf 'Could not find the default-route interface.\n' >&2
    exit 1
fi
BROADCAST="$(ifconfig "$IFACE" | awk '/inet / { for (i = 1; i <= NF; i++) if ($i == "broadcast") { print $(i + 1); exit } }')"
if [ -z "$BROADCAST" ]; then
    printf 'No IPv4 broadcast address found on %s.\n' "$IFACE" >&2
    exit 1
fi
printf 'Sending to %s on %s.\n' "$BROADCAST" "$IFACE"
printf '%s' 'Hello from CS240' | socat -u - "UDP4-DATAGRAM:${BROADCAST}:17429,broadcast"
```

#### Linux (Bash)

```bash
set -eu
IFACE="$(ip -4 route show default | awk 'NR == 1 { for (i = 1; i <= NF; i++) if ($i == "dev") { print $(i + 1); exit } }')"
if [ -z "$IFACE" ]; then
    printf 'Could not find the default-route interface.\n' >&2
    exit 1
fi
BROADCAST="$(ip -o -4 addr show dev "$IFACE" | awk '{ for (i = 1; i <= NF; i++) if ($i == "brd") { print $(i + 1); exit } }')"
if [ -z "$BROADCAST" ]; then
    printf 'No IPv4 broadcast address found on %s.\n' "$IFACE" >&2
    exit 1
fi
printf 'Sending to %s on %s.\n' "$BROADCAST" "$IFACE"
printf '%s' 'Hello from CS240' | socat -u - "UDP4-DATAGRAM:${BROADCAST}:17429,broadcast"
```

#### Windows PowerShell

This uses Windows' built-in .NET UDP client, so it does not require `socat`:

```powershell
$routes = Get-NetRoute -AddressFamily IPv4 -DestinationPrefix '0.0.0.0/0'
$route = $routes |
    ForEach-Object {
        $interfaceMetric = (Get-NetIPInterface -AddressFamily IPv4 -InterfaceIndex $_.InterfaceIndex).InterfaceMetric
        [pscustomobject]@{
            InterfaceIndex = $_.InterfaceIndex
            Metric = $_.RouteMetric + $interfaceMetric
        }
    } |
    Sort-Object Metric |
    Select-Object -First 1
if (-not $route) { throw 'Could not find an IPv4 default route.' }

$address = Get-NetIPAddress -AddressFamily IPv4 -InterfaceIndex $route.InterfaceIndex |
    Where-Object {
        $_.AddressState -eq 'Preferred' -and
        -not $_.SkipAsSource -and
        $_.PrefixLength -ge 1 -and $_.PrefixLength -le 30 -and
        $_.IPAddress -notlike '169.254.*'
    } |
    Select-Object -First 1
if (-not $address) { throw 'No usable IPv4 broadcast address found on the default-route interface.' }

$addressBytes = [System.Net.IPAddress]::Parse($address.IPAddress).GetAddressBytes()
$remaining = [int]$address.PrefixLength
for ($i = 0; $i -lt 4; $i++) {
    if ($remaining -ge 8) {
        $maskByte = 255
        $remaining -= 8
    } elseif ($remaining -gt 0) {
        $maskByte = [int](256 - [math]::Pow(2, 8 - $remaining))
        $remaining = 0
    } else {
        $maskByte = 0
    }
    $addressBytes[$i] = [byte]($addressBytes[$i] -bor (255 - $maskByte))
}
$BROADCAST = $addressBytes -join '.'
Write-Host "Sending to $BROADCAST on interface $($route.InterfaceIndex)."

$payload = [System.Text.Encoding]::UTF8.GetBytes('Hello from CS240')
$udp = [System.Net.Sockets.UdpClient]::new()
try {
    $udp.EnableBroadcast = $true
    [void]$udp.Send($payload, $payload.Length, $BROADCAST, 17429)
} finally {
    $udp.Dispose()
}
```

The commands use the default-route interface. If that is a VPN or another interface
without a subnet broadcast, select the intended LAN interface and determine its
broadcast address explicitly before sending. `/31` and `/32` IPv4 networks do not have
a directed broadcast address.

## What the addresses mean

- **Host IPv4** is this computer's address on the selected interface.
- **Network address** identifies the subnet; **network mask** and **CIDR** describe
  its size (for example, `192.168.1.0/24`).
- **Broadcast address** is the subnet's directed IPv4 broadcast destination.

Routers normally do not forward directed broadcasts, and Wi-Fi client isolation or
firewall rules may prevent delivery. A broadcast can reach other devices on the local
subnet, so only run it on a network where you have permission to send test traffic.

## Check whether the port is open

With the listener running, check for a local UDP socket bound to port 17429:

```bash
lsof -nP -iUDP:17429
```

On Linux, use `ss -lunp | grep ':17429'`. These show a local socket binding; they do
not prove a firewall or another machine can reach it.

To check one other host that you own or are authorized to test, you can scan just this
UDP port with Nmap:

```bash
sudo nmap -Pn -sU -p 17429 --reason 192.168.1.50
```

Replace `192.168.1.50` with that host's address. Do not scan a campus or other shared
network without permission. UDP has no handshake, and this listener does not reply to
Nmap's probe, so Nmap may report `open|filtered` even while the listener is running.
`closed` generally means the host returned an ICMP port-unreachable response. The
strongest practical check is that the receiver reports the test message; on that
receiver, `lsof` or `ss` confirms the local binding.

Use only one application receiver on the port at a time. Instead of the Python listener,
a netcat-compatible CLI may work:

```bash
# macOS/BSD netcat; option syntax varies by netcat implementation
nc -ul 17429
```

For packet capture, `tcpdump` and Wireshark's command-line tool, `tshark`, can filter
on the test port:

```bash
# Replace en0 with the interface shown by network_info.py
sudo tcpdump -ni en0 'udp port 17429'

# If tshark (installed with Wireshark) is available:
tshark -D
sudo tshark -i en0 -f 'udp port 17429'
```

Packet capture observes traffic on an interface; it is not an application listener and
does not by itself prove a process has bound the port. Capture only this lab traffic on
an interface and network you are authorized to monitor.

## What about campus Wi-Fi?

The broadcast address belongs to the local subnet/VLAN shown by `network_info.py`, not
to the whole campus. Routers normally do not forward directed broadcasts. Wi-Fi client
isolation, VLAN separation, access-point filtering, or broadcast rate limits can also
prevent other devices from receiving it. Follow campus IT policy and get permission
before sending broadcasts on a shared network.
