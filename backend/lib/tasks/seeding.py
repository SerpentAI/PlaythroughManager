import invoke
from invoke import task

from pony.orm import *
import lib.models


@task
def seed(ctx):
    seed_platforms()
    seed_sub_platforms()


def seed_platforms():
    platforms = [
        {"name": "PC"},
        {"name": "Playstation 4"},
        {"name": "Xbox One"},
        {"name": "Nintendo Switch"},
        {"name": "Nintendo Wii U"}
    ]

    list(map(lambda p: seed_platform(p), platforms))


@db_session
def seed_platform(p):
    platform = lib.models.Platform.get(name=p.get("name"))

    if platform is None:
        platform = lib.models.Platform(**p)
        commit()

        print(f"Successfully created Platform '{platform.name}'!")
    else:
        print(f"Platform '{platform.name}' already exists. Skipping!")


def seed_sub_platforms():
    sub_platforms = [
        {"name": "Windows", "platform": "PC"},
        {"name": "Mac", "platform": "PC"},
        {"name": "Linux", "platform": "PC"}
    ]

    list(map(lambda sp: seed_sub_platform(sp), sub_platforms))


@db_session
def seed_sub_platform(sp):
    sub_platform = lib.models.SubPlatform.get(name=sp.get("name"))

    if sub_platform is None:
        platform = lib.models.Platform.get(name=sp.get("platform"))
        sp["platform"] = platform

        sub_platform = lib.models.SubPlatform(**sp)
        commit()

        print(f"Successfully created SubPlatform '{sub_platform.name} => {sub_platform.platform.name}'!")
    else:
        print(f"SubPlatform '{sub_platform.name} => {sub_platform.platform.name}' already exists. Skipping!")


namespace = invoke.Collection("seeding")
namespace.add_task(seed)
