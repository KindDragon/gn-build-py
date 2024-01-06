from __future__ import annotations

import configparser
import os
import re
import urllib.request


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

    prev_git_revision = ""
    download_scripts = [""]
    for platform, details in platforms.items():
        url = f"https://chrome-infra-packages.appspot.com/p/gn/gn/{platform}/+/latest"
        fetched_details = fetch_details(url)

        if prev_git_revision == "":
            prev_git_revision = fetched_details["git_revision"]
        elif fetched_details["git_revision"] != prev_git_revision:
            raise Exception(
                f"Version mismatch for {platform}: expected {prev_git_revision}, got {fetched_details['git_revision']}"
            )

        download_script = f"""
[gn]
group = gn-binary
marker = {details["marker"]}
url = https://chrome-infra-packages.appspot.com/dl/gn/gn/{platform}/+/{fetched_details['instance_id']}
sha256 = {fetched_details['sha256']}
extract = zip
extract_path = {details["binary"]}
"""
        download_scripts.append(download_script.strip())

    return prev_git_revision, "\n".join(download_scripts)


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
    git_revision, download_scripts = generate_download_scripts()
    version = "0.0.1+" + git_revision[:12]
    create_setup_cfg(version, download_scripts)


if __name__ == "__main__":
    main()
