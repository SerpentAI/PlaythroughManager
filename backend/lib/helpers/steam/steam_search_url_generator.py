from lib.config import config


class SteamSearchURLGenerator:
    PRODUCT_TYPES = {
        "Games":998,
        "DLC": 21
    }

    SORT_OPTIONS = {
        "Relevance": "_ASC",
        "Release Date": "Released_DESC",
        "Name": "Name_ASC",
        "Lowest Price": "Price_ASC",
        "Highest Price": "Price_DESC",
        "User Reviews": "Reviews_DESC"
    }

    @property
    def product_types(self):
        return list(self.__class__.PRODUCT_TYPES)

    @property
    def sort_options(self):
        return list(self.__class__.SORT_OPTIONS)

    def generate(self, page=1, product_types=None, sort_option="Name"):
        if product_types is None:
            product_types = ["Games"]

        valid_page = self.validate_page(page) or 1
        valid_product_types = self.validate_product_types(product_types) or ["Games"]
        valid_sort_option = self.validate_sort_option(sort_option) or "Name"

        return "%s/search?%s&%s&%s" % (
            config["product_providers"]["steam"]["store"]["base_url"],
            self._sort_by_param(valid_sort_option),
            self._product_types_param(valid_product_types),
            self._page_param(valid_page)
        )

    def validate_product_types(self, product_types):
        if type(product_types) != list:
            return list()

        return list(filter(lambda pt: pt in self.product_types, product_types))

    def validate_sort_option(self, sort_option):
        return sort_option if sort_option in self.sort_options else None

    @staticmethod
    def validate_page(page):
        try:
            page = int(page)
        except Exception:
            page = 1

        return page

    @staticmethod
    def _sort_by_param(sort_option):
        return "sort_by=%s" % SteamSearchURLGenerator.SORT_OPTIONS.get(sort_option)

    @staticmethod
    def _product_types_param(product_types):
        return "category1=%s" % ",".join(list(map(lambda pt: str(SteamSearchURLGenerator.PRODUCT_TYPES.get(pt)), product_types)))

    @staticmethod
    def _page_param(page):
        return "page=%d" % page
