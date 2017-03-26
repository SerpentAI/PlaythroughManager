import invoke
from invoke import task

from pony.orm import *
import lib.models


@task
def temp(ctx):
    pass


namespace = invoke.Collection("product_fetching")

# namespace.add_task(discover_all)

