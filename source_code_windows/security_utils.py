#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Security validation utilities for NetworkManager tool."""

import ipaddress
import re
import os
import tempfile


def validate_ipv4(address: str) -> bool:
    """Validate if string is a valid IPv4 address."""
    try:
        ipaddress.IPv4Address(address)
        return True
    except (ipaddress.AddressValueError, ValueError):
        return False


def validate_hostname(hostname: str) -> bool:
    """Validate if string is a valid hostname or domain."""
    if (not hostname or len(hostname) > 253 or '%' in hostname
            or any(ord(char) < 32 or ord(char) == 127 for char in hostname)):
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
    if re.fullmatch(r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?', hostname):
        return True
    
    return False


def validate_interface_name(ifname: str) -> bool:
    """Validate network interface name (Linux: max 15 chars, alphanumeric, hyphen, underscore, dot)."""
    if not ifname or len(ifname) > 15:
        return False
    return ifname not in ('.', '..') and bool(re.fullmatch(r'[a-zA-Z0-9_][a-zA-Z0-9:._-]*', ifname))


def validate_profile_name(profile_name: str) -> bool:
    """Validate NetworkManager profile name."""
    if not profile_name or len(profile_name) > 255:
        return False
    # Reject control characters, including null bytes and line breaks.
    return not any(ord(char) < 32 or ord(char) == 127 for char in profile_name)


def validate_netmask(mask: str) -> bool:
    """Accept a contiguous dotted IPv4 netmask."""
    if not validate_ipv4(mask):
        return False
    try:
        return str(ipaddress.IPv4Network('0.0.0.0/' + mask).netmask) == mask
    except ValueError:
        return False


def save_report(directory, content, prefix, timestamp):
    """Create a private, unique report without following an existing file link."""
    safe_prefix = re.sub(r'[^A-Za-z0-9_-]', '_', prefix)[:80] or 'Report'
    fd, path = tempfile.mkstemp(prefix=f'{safe_prefix}_{timestamp}_', suffix='.txt', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as report:
            report.write(content)
    except BaseException:
        os.unlink(path)
        raise
    return path
