# gn-build-py

A Python wrapper to provide a pip-installable [GN](https://gn.googlesource.com/gn/+/main/docs/reference.md#cmd_format) binary, designed for use with [pre-commit](http://pre-commit.com). This tool simplifies the process of installing and using GN for source code formatting in projects that utilize pre-commit hooks.

## Using gn-build-py as a Pre-commit Hook

To use `gn-build-py` as a pre-commit hook for formatting GN files, add the following configuration to your `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/KindDragon/gn-build-py.git
    rev: ''
    hooks:
    -   id: gn-build-py
```

Than run `pre-commit autoupdate` to update config to latest available gn build version.

This configuration ensures that the GN binary is available and used by pre-commit to format GN files in your repository.

## Building and Publishing a New Package Version

The `build_and_push.sh` script is used to automate the process of building, testing, and deploying new versions of `gn-build-py`. It handles generating the latest `setup.cfg`, building the package, running tests, committing changes, and tagging the release.

### Prerequisites

- Ensure you have `python`, `pip`, and `git` installed.
- Install `tox` for running tests: `pip install tox`.

### Steps to Build and Publish

1. **Run the Script**: Execute `build_and_push.sh` from the root directory of the project.

    ```bash
    ./build_and_push.sh
    ```

2. **Automated Process**: The script will:
    - Generate the latest `setup.cfg` with updated GN version.
    - Build the package.
    - Run tests using `tox`.
    - Commit the changes to the repository.
    - Tag the commit with the new version.
    - Push the commit and tag to the repository.

3. **Upload to PyPI** (Optional): If you wish to distribute the package via PyPI, use [twine](https://pypi.org/project/twine/) to upload the distributions:

    ```bash
    twine upload dist/*
    ```

    Ensure you have the necessary credentials for PyPI and have tested the package thoroughly.
