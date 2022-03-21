# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

import argparse
import json
import paramiko

from commands.fwnat import FWNat
from commands.dns import DNS
from commands.files import Files
from commands.fwrules import FW
from commands.ports import Ports
from commands.proxy import Proxy
from commands.scheduler import Scheduler
from commands.socks import Socks
from commands.users import Users
from commands.version import Version

search_list = []


def main(args):
    if args.ip == "" and args.list == "" and args.discover == "":
        print("error: At least one argument is required: -i, -l or -d.")
    else:
        if (
            (args.ip != "" and args.list != "")
            or (args.ip != "" and args.discover != "")
            or (args.list != "" and args.discover != "")
        ):
            print("error: Only one argument -i, -l or -d is permited.")
        elif args.ip != "":
            search_list.append(args.ip)
            test_router(args.port, args.userName, args.password)
        elif args.list != "":
            with open(args.list, "r") as router_list:
                for line in router_list:
                    for r in line.split(","):
                        search_list.append(r.strip(' '))
            test_router(args.port, args.userName, args.password)
        else:
            search_net(args.discover, args.port, args.userName, args.password)
            test_router(args.port, args.userName, args.password)


def print_txt_results(res):
    for command in res:
        print(f"{command}:")
        for item in res[command]:
            if res[command][item]:
                print(f"\t{item}:")
                if type(res[command][item]) == list:
                    data = "\n\t\t".join(json.dumps(i) for i in res[command][item])
                else:
                    data = res[command][item]
                print(f"\t\t{data}")


def list_peers(r, port, username, password):
    rots = []
    with paramiko.SSHClient() as ssh_client:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(
                hostname=r, port=port, username=username, password=password
            )
            stdin, stdout, stderr = ssh_client.exec_command("/ip route print")
            outlines = stdout.readlines()
            for i in range(3, len(outlines)):
                n = outlines[i].split("  ")
                r = n[len(n) - 2]
                if "." in r:
                    rots.append(r.strip(" "))
        except:
            pass
    return rots


def search_net(r, port, username, password):
    if r not in search_list:
        search_list.append(r)
    peers = list_peers(r, port, username, password)
    if len(peers) > 0:
        for p in peers:
            if p not in search_list:
                search_list.append(p)
                search_net(p, port, username, password)


def test_router(port, username, password):
    for ip in search_list:
        verify(ip, port, username, password)


def verify(ip, port, username, password):
    all_data = {}
    commands = [
        Version(),
        Scheduler(),
        Files(),
        FWNat(),
        Proxy(),
        Socks(),
        DNS(),
        Users(),
        Ports(),
        FW(),
    ]

    print(f"Mikrotik ip address: {ip}\n")

    with paramiko.SSHClient() as ssh_client:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            ssh_client.connect(
                hostname=ip, port=port, username=username, password=password
            )
            for command in commands:
                res = command.run_ssh(ssh_client)
                all_data[command.__name__] = res

            if args.J:
                print(json.dumps(all_data, indent=4))
            else:
                print_txt_results(all_data)
        except:
            print("Conection error")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--ip", help="The tested Mikrotik IP address", default="")
    parser.add_argument(
        "-l",
        "--list",
        help="Comma separated tested Mikrotiks IPs address list file",
        default="",
    )
    parser.add_argument(
        "-d", "--discover", help="Discover mode from root router IP", default=""
    )
    parser.add_argument(
        "-p", "--port", help="The tested Mikrotik SSH port", required=True
    )
    parser.add_argument(
        "-u", "--userName", help="User name with admin Permissions", required=True
    )
    parser.add_argument(
        "-ps", "--password", help="The password of the given user name", default=""
    )
    parser.add_argument(
        "-J", help="Print the results as json format", action="store_true"
    )
    args = parser.parse_args()

    main(args)
