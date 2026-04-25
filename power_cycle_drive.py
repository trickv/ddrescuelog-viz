#!/usr/bin/env python3
"""
Power cycle a hard drive using Home Assistant relay control and SCSI rescanning.
"""

import os
import sys
import time
import requests
from pathlib import Path


# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RESET = '\033[0m'


def get_hass_config():
    """Get Home Assistant configuration from environment."""
    hass_url = "https://hass.vanstaveren.us"
    hass_token = os.environ.get('HASS_LLAC')

    if not hass_token:
        print(f"{RED}ERROR: HASS_LLAC environment variable not set{RESET}")
        sys.exit(1)

    return hass_url, hass_token


def call_hass_service(hass_url, token, service, entity_id):
    """Call a Home Assistant service."""
    domain, service_name = service.split('.')
    url = f"{hass_url}/api/services/{domain}/{service_name}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    data = {"entity_id": entity_id}

    try:
        response = requests.post(url, headers=headers, json=data, timeout=10)
        response.raise_for_status()
        print(f"{GREEN}✓{RESET} Called {service} on {entity_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"{RED}ERROR: Failed to call Home Assistant service: {e}{RESET}")
        return False


def scsi_rescan(host_number):
    """Trigger SCSI bus rescan."""
    scan_path = f"/sys/class/scsi_host/host{host_number}/scan"

    try:
        with open(scan_path, 'w') as f:
            f.write("- - -")
        print(f"{GREEN}✓{RESET} SCSI rescan triggered on host{host_number}")
        return True
    except PermissionError:
        print(f"{RED}ERROR: Permission denied writing to {scan_path}. Run with sudo?{RESET}")
        return False
    except Exception as e:
        print(f"{RED}ERROR: Failed to rescan SCSI bus: {e}{RESET}")
        return False


def check_device_exists(device_path, timeout=60):
    """Check if device exists, optionally waiting with timeout."""
    if Path(device_path).exists():
        print(f"{GREEN}✓{RESET} Device {device_path} exists")
        return True

    if timeout > 0:
        print(f"{YELLOW}⚠{RESET} Device {device_path} not found, waiting {timeout} seconds...")
        time.sleep(timeout)

        if Path(device_path).exists():
            print(f"{GREEN}✓{RESET} Device {device_path} now exists")
            return True

    return False


def main():
    """Main power cycle routine."""
    # Configuration
    relay_entity = "switch.esp46a646_rs41_dfm17_relay_d2"
    scsi_host = 1
    target_device = "/dev/sdb"

    hass_url, hass_token = get_hass_config()

    print(f"\n{YELLOW}Starting hard drive power cycle procedure...{RESET}\n")

    # Step 1: Turn off power
    print("Step 1: Turning off power to hard drive...")
    if not call_hass_service(hass_url, hass_token, "switch.turn_off", relay_entity):
        sys.exit(1)

    # Step 2: Wait 10 seconds
    print("Step 2: Waiting 10 seconds...")
    time.sleep(10)

    # Step 3: SCSI rescan (power off)
    print("Step 3: Rescanning SCSI bus (power off)...")
    if not scsi_rescan(scsi_host):
        sys.exit(1)

    # Step 4: Turn on power
    print("Step 4: Turning on power to hard drive...")
    if not call_hass_service(hass_url, hass_token, "switch.turn_on", relay_entity):
        sys.exit(1)

    # Step 5: Wait 10 seconds
    print("Step 5: Waiting 10 seconds for drive to spin up...")
    time.sleep(10)

    # Step 6: SCSI rescan (power on)
    print("Step 6: Rescanning SCSI bus (power on)...")
    if not scsi_rescan(scsi_host):
        sys.exit(1)

    # Step 7: Verify device exists
    print(f"Step 7: Verifying {target_device} exists...")
    if not check_device_exists(target_device, timeout=0):
        print(f"{YELLOW}⚠{RESET} Device not found on first check, waiting 60 seconds...")
        time.sleep(60)

        if not check_device_exists(target_device, timeout=0):
            # Device still doesn't exist - show error and sleep indefinitely
            print(f"\n{RED}{'='*60}{RESET}")
            print(f"{RED}{'='*60}{RESET}")
            print(f"{RED}CRITICAL ERROR: Device {target_device} not found!{RESET}")
            print(f"{RED}The hard drive did not come online after power cycle.{RESET}")
            print(f"{RED}{'='*60}{RESET}")
            print(f"{RED}{'='*60}{RESET}\n")

            print(f"{YELLOW}Sleeping indefinitely. Press Ctrl+C to exit.{RESET}\n")

            try:
                while True:
                    time.sleep(3600)  # Sleep in 1-hour chunks
            except KeyboardInterrupt:
                print(f"\n{YELLOW}Interrupted by user{RESET}")
                sys.exit(1)

    print(f"\n{GREEN}✓ Power cycle completed successfully!{RESET}\n")


if __name__ == "__main__":
    main()
