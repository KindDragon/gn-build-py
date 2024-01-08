from __future__ import annotations

import configparser
import os
import re
import subprocess
import sys
import urllib.request
import zipfile
from io import BytesIO
from pathlib import Path


def fetch_details(url: str):
    with urllib.request.urlopen(url) as response:
        html = response.read().decode("utf-8")

    sha_match = re.search(
        r'SHA256</b></td>\s*<td class="user-select-all">([a-f0-9]{64})</td>', html
    )
    instance_id_match = re.search(
        r'Instance ID</b></td>\s*<td class="user-select-all">([^<]+)</td>', html
    )
    git_revision_match = re.search(r"git_revision:([a-f0-9]{40})", html)

    if not sha_match or not instance_id_match or not git_revision_match:
        raise Exception("Details not found in the page.")

    return {
        "sha256": sha_match.group(1),
        "instance_id": instance_id_match.group(1),
        "git_revision": git_revision_match.group(1),
    }


def generate_download_scripts():
    platforms = {
        "linux-amd64": {
            "binary": "gn",
            "marker": 'sys_platform == "linux" and platform_machine == "x86_64"',
        },
        "linux-arm64": {
            "binary": "gn",
            "marker": 'sys_platform == "linux" and platform_machine == "aarch64"',
        },
        "mac-amd64": {
            "binary": "gn",
            "marker": 'sys_platform == "darwin" and platform_machine == "x86_64"',
        },
        "mac-arm64": {
            "binary": "gn",
            "marker": 'sys_platform == "darwin" and platform_machine == "arm64"',
        },
        "windows-amd64": {
            "binary": "gn.exe",
            "marker": 'sys_platform == "win32" and platform_machine == "AMD64"',
        },
    }

    fetched_details = {}
    prev_git_revision = ""
    download_scripts = [""]
    for platform, details in platforms.items():
        url = f"https://chrome-infra-packages.appspot.com/p/gn/gn/{platform}/+/latest"
        platform_details = fetch_details(url)

        if prev_git_revision == "":
            prev_git_revision = platform_details["git_revision"]
        elif platform_details["git_revision"] != prev_git_revision:
            raise Exception(
                f"Version mismatch for {platform}: expected {prev_git_revision}, got {platform_details['git_revision']}"
            )

        download_script = f"""
[gn]
group = gn-binary
marker = {details["marker"]}
url = https://chrome-infra-packages.appspot.com/dl/gn/gn/{platform}/+/{platform_details['instance_id']}
sha256 = {platform_details['sha256']}
extract = zip
extract_path = {details["binary"]}
"""
        download_scripts.append(download_script.strip())
        fetched_details[platform] = platform_details

    return prev_git_revision, "\n".join(download_scripts), fetched_details


def download_and_extract_gn(url: str, binary_name: str):
    build_path = Path("build/temp")
    build_path.mkdir(parents=True, exist_ok=True)

    with urllib.request.urlopen(url) as response:
        with zipfile.ZipFile(BytesIO(response.read())) as zip_file:
            zip_file.extract(binary_name, path=build_path)

    return build_path / binary_name


def get_gn_version(binary_name: str):
    result = subprocess.run([binary_name, "--version"], capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Error running {binary_name}: {result.stderr}")

    match = re.search(r"(\d+) \((\w+)\)", result.stdout.strip())
    if not match:
        raise Exception(f"Unable to parse GN version output: {result.stdout.strip()}")

    version, git_revision = match.groups()
    return version, git_revision


def create_setup_cfg(version, download_scripts):
    config = configparser.ConfigParser()

    # Check if setup.cfg already exists
    if os.path.exists("setup.cfg"):
        config.read("setup.cfg")
        existing_version = config.get("metadata", "version", fallback=None)
        if existing_version == version:
            raise Exception(f"Error: setup.cfg already has the same version {version}")

    config.read("setup.cfg.template")

    # Replace placeholders in the template
    config["metadata"]["version"] = version

    # Add the dynamically generated download_scripts section
    config.add_section("setuptools_download")
    config.set("setuptools_download", "download_scripts", download_scripts)

    # Write the new setup.cfg
    with open("setup.cfg", "w") as config_file:
        config.write(config_file)


def main():
    git_revision, download_scripts, all_fetched_details = generate_download_scripts()

    current_platform = sys.platform
    platform_machine = os.uname().machine
    binary_name = "gn" if current_platform != "win32" else "gn.exe"
    platform_key = f"{current_platform}-{platform_machine}"
    platform_details = {
        "linux-x86_64": "linux-amd64",
        "linux-aarch64": "linux-arm64",
        "darwin-x86_64": "mac-amd64",
        "darwin-arm64": "mac-arm64",
        "win32-AMD64": "windows-amd64",
    }.get(platform_key)

    if not platform_details:
        raise Exception(f"Unsupported platform: {platform_key}")

    platform_specific_details = all_fetched_details.get(platform_details)
    if not platform_specific_details:
        raise Exception(f"No details found for platform: {platform_key}")

    download_url = f"https://chrome-infra-packages.appspot.com/dl/gn/gn/{platform_details}/+/{platform_specific_details['instance_id']}?format=zip"
    download_and_extract_gn(download_url, binary_name)

    version, gn_git_revision = get_gn_version(binary_name)
    print(f"GN version: {version} ({gn_git_revision})")
    assert git_revision[:12] == gn_git_revision

    create_setup_cfg(version, download_scripts)


if __name__ == "__main__":
    main()
