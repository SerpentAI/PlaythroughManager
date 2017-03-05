import subprocess

import invoke
from invoke import task


# Task Collection Imports

import lib.tasks.seeding


@task
def version():
    version_number = subprocess.check_output(["cat", "VERSION"]).decode("utf-8")
    revision = subprocess.check_output(["git", "log", "--pretty=format:%H", "-n", "1"]).decode("utf-8")

    print("PlaythroughManager Version: %s - Revision: %s" % (version_number, revision))

# Invoke Namespace Definition
namespace = invoke.Collection()

namespace.add_task(version)

#namespace.add_collection(lib.tasks.seeding.namespace)