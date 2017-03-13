import warnings

from redis import StrictRedis
from rq import Queue

from lib.config import config


class ProductFetcherError(BaseException):
    pass


class ProductFetcher:
    def __init__(self, **kwargs):
        self.redis_client = StrictRedis(
            host=config["redis"]["host"],
            port=config["redis"]["port"],
            db=config["redis"]["databases"]["jobs"]
        )

        self.queue = Queue("product_fetching", connection=self.redis_client)

    # Discovery
    def discover(self, discovery_type="Recent", product_type="Games", **kwargs):
        if discovery_type not in ["Recent", "All"]:
            warnings.warn("Invalid discovery_type provided. Defaulting to 'Recent'")
            discovery_type = "Recent"

        if product_type not in ["Games", "DLC"]:
            warnings.warn("Invalid product_type provided. Defaulting to 'Games'")
            discovery_type = "Games"

        if discovery_type == "All":
            self.discover_all(product_type=product_type, **kwargs)
        elif discovery_type == "Recent":
            self.discover_recent(product_type=product_type, **kwargs)

    def discover_all(self, product_type="Games", **kwargs):
        raise NotImplementedError()

    def discover_recent(self, product_type="Games", **kwargs):
        raise NotImplementedError()

    # Handlers
    def on_product_discovered(self, product_type="Games", **kwargs):
        raise NotImplementedError()

    def create_product(self, product_type="Games", **kwargs):
        raise NotImplementedError()

    def update_product(self, product_types="Games", **kwargs):
        raise NotImplementedError()
