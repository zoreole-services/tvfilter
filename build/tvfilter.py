#!/usr/bin/env python3

import boto3
import ipaddress
import os
import sys
import time

# AWS Authentication Configuration
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")

# S3 Information Configuration
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME")
S3_OBJECT_KEY_PATH = os.getenv("S3_OBJECT_KEY_PATH")
S3_OBJECT_FILE_NAME = os.getenv("S3_OBJECT_FILE_NAME")
S3_OBJECT_KEY = f"{S3_OBJECT_KEY_PATH}/{S3_OBJECT_FILE_NAME}"

# Local ISP IPv4 & IPv6 networks
MY_SUPERNETS = os.getenv("MY_SUPERNETS", "").split()

# Maximum IP prefixes for IP blocking list
# (Default = 3000)
MAX_PREFIXES = int(os.getenv("MAX_PREFIXES"))

# Blackhole BGP community
# (Default = 65535:666)
BLACKHOLE_COMMUNITY = os.getenv("BLACKHOLE_COMMUNITY")

# Polling interval for updating BGP announcements in seconds
# (Default = 30)
POLLING_INTERVAL = int(os.getenv("POLLING_INTERVAL"))

# S3 Session Creation
s3_session = boto3.Session(
    aws_access_key_id = AWS_ACCESS_KEY_ID,
    aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
    region_name = AWS_REGION
)

# S3 Resource Creation
s3_resource = s3_session.resource('s3')
s3_object = s3_resource.Object(S3_BUCKET_NAME, S3_OBJECT_KEY)


def send(message):
    sys.stdout.write(f"{message}\n")
    sys.stdout.flush()
    resp = sys.stdin.readline()
    if not resp:
        sys.exit(0)
    resp = resp.strip()
    if resp == "shutdown":
        sys.exit(0)
    if resp != "done":
        print(f"[EXABGP] '{message}' -> {resp}", file=sys.stderr, flush=True)

def is_ip_in_networks(address, networks):
    ip = ipaddress.ip_network(address)
    for network in networks:
        net = ipaddress.ip_network(network)
        if ip.version == net.version and ip.subnet_of(net):
            return True
    return False

def sort_ip(addresses):
    ipv4_list, ipv6_list = ipv4_ipv6_split(addresses)
    ipv4_sorted_list = sorted(ipv4_list, key=lambda ip: ipaddress.ip_network(ip))
    ipv6_sorted_list = sorted(ipv6_list, key=lambda ip: ipaddress.ip_network(ip))
    return ipv4_sorted_list + ipv6_sorted_list

def ipv4_ipv6_split(addresses):
    ipv4_list = []
    ipv6_list = []
    for address in addresses:
        try:
            net = ipaddress.ip_network(address)
            if net.version == 4:
                ipv4_list.append(address)
            elif net.version == 6:
                ipv6_list.append(address)
        except ValueError:
            continue
    return ipv4_list, ipv6_list

def route_filter(routes):
    filtered_routes = set()
    for route in routes:
        try:
            ip = ipaddress.ip_network(route)
            # Check if the number of accepted routes is within the specified maximum prefixes number
            if len(filtered_routes) <= MAX_PREFIXES:
                # Check to filter out prohibited IP addresses
                if ( not ip.is_multicast and
                        not ip.is_unspecified and
                        not ip.is_reserved and
                        not ip.is_link_local and
                        not ip.is_loopback and
                        not ip.is_private and
                        not (ip.version == 4 and ip.prefixlen < 32) and
                        not (ip.version == 6 and ip.prefixlen < 128) and
                        not is_ip_in_networks(ip, MY_SUPERNETS)):
                    filtered_routes.add(route)
        except ValueError:
            continue
    return sort_ip(filtered_routes)

# Function to create the full command for ExaBGP
def announce(command, route):
    ip = ipaddress.ip_address(route.split('/')[0])
    if ip.version == 4:
        return f"{command} route {route} next-hop self community {BLACKHOLE_COMMUNITY}"
    elif ip.version == 6:
        return f"{command} route {route} next-hop self community {BLACKHOLE_COMMUNITY}"

# Function to get IP list from S3 bucket
def get_list():
    try:
        body = s3_object.get()['Body'].read().decode('utf-8')
        return set(
            line.strip()
            for line in body.splitlines()
            if line.strip()
        )
    except Exception as e:
        print(f"[S3 ERROR] {e}", file=sys.stderr, flush=True)
        return None

if __name__ == '__main__':
    current_list = []
    while True:
        s3_list = get_list()

        # Check whether the s3_list was well retrieved.
        if s3_list is None:
            time.sleep(POLLING_INTERVAL)
            continue
        s3_list_filtered = route_filter(s3_list)

        for route in s3_list_filtered:
            if route not in current_list:
                send(announce('announce', route))
                current_list.append(route)
                current_list = sort_ip(current_list)
        for route in current_list[:]:
            if route not in s3_list_filtered:
                send(announce('withdraw', route))
                current_list.remove(route)
                current_list = sort_ip(current_list)
        time.sleep(POLLING_INTERVAL)
