"""Static rule fixtures only. Semgrep reads this file; do not execute it."""

import os
from os import system as shell
import shutil
import subprocess


def rejected_commands(filename):
    # ruleid: python-no-os-system
    os.system(f"convert {filename} -resize 50% output.png")

    # The policy forbids even a constant shell command.
    # ruleid: python-no-os-system
    os.system("echo example")

    # Imported aliases must not bypass the policy.
    # ruleid: python-no-os-system
    shell("echo example")


def accepted_operations(source, destination):
    # ok: python-no-os-system
    shutil.move(source, destination)

    # ok: python-no-os-system
    subprocess.run(["python3", "--version"], check=True)

    # A string containing the name is not a function call.
    # ok: python-no-os-system
    return "Avoid os.system in application code"
