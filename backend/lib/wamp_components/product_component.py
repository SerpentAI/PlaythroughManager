import asyncio

from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner
from autobahn.wamp.types import RegisterOptions, SubscribeOptions
from autobahn.wamp import auth

from lib.config import config

from pony.orm import *
from lib.models import *

import json


class ProductComponent:
    @classmethod
    def run(cls):
        print(f"Starting {cls.__name__}...")

        url = "ws://%s:%s" % (config["crossbar"]["host"], config["crossbar"]["port"])

        runner = ApplicationRunner(url=url, realm=config["crossbar"]["realm"])
        runner.run(ProductWAMPComponent)


class ProductWAMPComponent(ApplicationSession):
    def __init__(self, c=None):
        super().__init__(c)

    def onConnect(self):
        self.join(config["crossbar"]["realm"], ["wampcra"], config["crossbar"]["auth"]["username"])

    def onDisconnect(self):
        print("Disconnected from Crossbar!")

    def onChallenge(self, challenge):
        secret = config["crossbar"]["auth"]["password"]
        signature = auth.compute_wcs(secret.encode('utf8'), challenge.extra['challenge'].encode('utf8'))

        return signature.decode('ascii')

    async def onJoin(self, details):
        # RPC Endpoints

        @db_session
        def fetch_product(product_provider_name, product_name):
            product_provider = ProductProvider.get(name=product_provider_name)

            if product_provider is None:
                return {"OK": False, "messages": ["Invalid Product Provider..."]}

            product = Product.get(lambda p: product_provider in p.product_providers and p.name == product_name)

            if product is None:
                return {"OK": False, "messages": ["Invalid Product..."]}

            return {"OK": True, "product": product.as_json()}

        @db_session
        def fetch_select_products():
            product_images = ProductImage.select(lambda pi: pi.type == "icon_large")[:]
            product_names = list(sorted(list(map(lambda pi: pi.product.name, product_images))))

            return {"product_names": product_names}

        await self.register(fetch_product, f"{config['crossbar']['realm']}.fetch_product", options=RegisterOptions(invoke=u'roundrobin'))
        await self.register(fetch_select_products, f"{config['crossbar']['realm']}.fetch_select_products", options=RegisterOptions(invoke=u'roundrobin'))
