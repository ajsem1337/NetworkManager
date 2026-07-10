#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Security validation utilities for NetworkManager tool."""

import ipaddress
import re


def validate_ipv4(address: str) -> bool:
    """Validate if string is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(address)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def validate_hostname(hostname: str) -> bool:
    """Validate if string is a valid hostname or domain."""
    if not hostname or len(hostname) > 253:
        return False
    
    # Allow IPv4, IPv6, and hostnames
    if validate_ipv4(hostname):
        return True
    
    try:
        ipaddress.IPv6Address(hostname)
        return True
    except (ipaddress.AddressValueError, ValueError):
        pass
    
    # RFC 1123: alphanumeric, hyphens, dots. No leading/trailing hyphen/dot
    if re.match(r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?$', hostname):
        return True
    
    return False


def validate_interface_name(ifname: str) -> bool:
    """Validate network interface name (Linux: max 15 chars, alphanumeric, hyphen, underscore, dot)."""
    if not ifname or len(ifname) > 15:
        return False
    return bool(re.match(r'^[a-zA-Z0-9:._-]+$', ifname))


def validate_profile_name(profile_name: str) -> bool:
    """Validate NetworkManager profile name."""
    if not profile_name or len(profile_name) > 255:
        return False
    # Allow most characters except null bytes
    return '\x00' not in profile_name
