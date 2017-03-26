from lib.product_fetcher import ProductFetcher, ProductFetcherError

from lib.helpers.steam.steam_search_url_generator import SteamSearchURLGenerator

from selenium.webdriver.chrome.webdriver import WebDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementNotVisibleException

from selenium_respectful import RespectfulWebdriver

from pyvirtualdisplay import Display

from pony.orm import *

import lib.models
import uuid
import re


from datetime import datetime

import requests
from requests_respectful import RespectfulRequester

from dateutil.parser import parse as datetime_parse

from lib.config import config


class SteamProductFetcher(ProductFetcher):

    @db_session
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.product_provider_uuid = lib.models.ProductProvider.get(name="Steam").uuid
        self.platform_uuid = lib.models.Platform.get(name="PC").uuid

    def discover_all(self, product_type="Games", **kwargs):
        product_ids = self._fetch_product_ids(
            product_type=product_type,
            sort_option=kwargs.get("sort_option", "Name")
        )

        for product_id in product_ids:
            self.on_product_discovered(product_type=product_type, product_id=product_id, **kwargs)

    def discover_recent(self, product_type="Games", **kwargs):
        product_ids = self._fetch_product_ids(
            product_type=product_type,
            sort_option=kwargs.get("sort_option", "Name"),
            max_page=kwargs.get("max_page", 5)
        )

        for product_id in product_ids:
            self.on_product_discovered(product_type=product_type, product_id=product_id, **kwargs)

    @db_session
    def on_product_discovered(self, product_type="Games", **kwargs):
        product_provider = lib.models.ProductProvider.get(uuid=self.product_provider_uuid)
        kwargs["product_provider"] = product_provider

        product_query = lambda p: p.external_id == kwargs.get("product_id") and product_provider in p.product_providers
        product = lib.models.Product.get(product_query)

        if product is None:
            self.create_product(product_type=product_type, **kwargs)
        else:
            kwargs["product"] = product
            self.update_product(product_type=product_type, **kwargs)

    @db_session
    def create_product(self, product_type="Games", **kwargs):
        platform = lib.models.Platform.get(uuid=self.platform_uuid)

        product = lib.models.Product(
            type=product_type,
            external_id=kwargs.get("product_id"),
            platform=platform,
            product_providers=[kwargs.get("product_provider")]
        )

        commit()

        self.enqueue_product_update_jobs(product)

    @db_session
    def update_product(self, product_type="Games", **kwargs):
        self.enqueue_product_update_jobs(kwargs["product"])

    def enqueue_product_update_jobs(self, product):
        self.queue.enqueue(self.__class__.update_product_from_big_picture_api, str(product.uuid))
        self.queue.enqueue(self.__class__.update_product_from_store_page, str(product.uuid))

        steam_web_api_job = self.queue.enqueue(self.__class__.update_product_from_web_api, str(product.uuid))
        self.queue.enqueue(self.__class__.update_achievement_global_percents_from_web_api, str(product.uuid), depends_on=steam_web_api_job)

    @classmethod
    @db_session
    def update_product_from_web_api(cls, product_uuid):
        product = lib.models.Product.get(uuid=uuid.UUID(product_uuid))

        if product is None:
            raise ProductFetcherError("Invalid product provided!")

        requester = RespectfulRequester()
        requester.register_realm("Steam Web API", max_requests=200, timespan=60)

        url = f"{config['product_providers']['steam']['web_api']['base_url']}/ISteamUserStats/GetSchemaForGame/v2/" \
              f"?key={config['product_providers']['steam']['web_api']['api_key']}&appid={product.external_id}"

        http_response = requester.get(url, realms=["Steam Web API"], wait=True)

        if http_response.status_code != 200:
            raise ProductFetcherError("Invalid response from the Steam Web API...")

        json_response = http_response.json()

        cls.update_product_achievements(product, json_response)

    @classmethod
    @db_session
    def update_product_from_big_picture_api(cls, product_uuid):
        product = lib.models.Product.get(uuid=uuid.UUID(product_uuid))

        if product is None:
            raise ProductFetcherError("Invalid product provided!")

        requester = RespectfulRequester()
        requester.register_realm("Steam Big Picture API", max_requests=40, timespan=60)

        url = f"{config['product_providers']['steam']['big_picture_api']['base_url']}/appdetails?appids={product.external_id}"
        http_response = requester.get(url, realms=["Steam Web API"], wait=True)

        if http_response.status_code != 200:
            raise ProductFetcherError("Invalid response from the Steam Big Picture API...")

        json_response = http_response.json()

        data = json_response.get(product.external_id).get("data")

        if data is None:
            return None

        cls.update_product_basic_information(product, data)
        cls.update_product_sub_platforms(product, data)
        cls.update_product_developers(product, data)
        cls.update_product_publishers(product, data)
        cls.update_product_genres(product, data)
        cls.update_product_categories(product, data)
        cls.update_product_parent_children(product, data)

    @classmethod
    @db_session
    def update_product_from_store_page(cls, product_uuid):
        product = lib.models.Product.get(uuid=uuid.UUID(product_uuid))

        if product is None:
            raise ProductFetcherError("Invalid product provided!")

        display = Display(visible=False, size=(800, 600))
        display.start()

        driver = RespectfulWebdriver(webdriver=WebDriver("vendor/chromedriver"))

        try:
            driver.register_realm("Steam Store", max_requests=100, timespan=60)

            driver.get(f"{config['product_providers']['steam']['store']['base_url']}", realms=["Steam Store"], wait=True)

            driver.add_cookie({"name": "birthtime", "value": "0", "domain": "store.steampowered.com"})
            driver.add_cookie({"name": "lastagecheckage", "value": "1-January-1900", "domain": "store.steampowered.com"})

            url = f"{config['product_providers']['steam']['store']['base_url']}/app/{product.external_id}"

            driver.get(url, realms=["Steam Store"], wait=True)

            try:
                description_element = driver.find_element_by_class_name("game_description_snippet")
                description = description_element.text
            except NoSuchElementException:
                description = ""

            try:
                tag_plus_button_element = driver.find_element_by_css_selector(".popular_tags .add_button")
                tag_plus_button_element.click()

                tag_elements = driver.find_elements_by_css_selector("div.app_tag_control > a")

                tags = list()

                for tag_element in tag_elements:
                    tags.append(tag_element.text)

                close_element = driver.find_element_by_class_name("newmodal_close")
                close_element.click()
            except NoSuchElementException:
                tags = list()
            except ElementNotVisibleException:
                tags = list()

            try:
                screenshot_elements = driver.find_elements_by_css_selector("div.highlight_strip_screenshot img")
                screenshot_urls = list()

                for screenshot_element in screenshot_elements:
                    url = screenshot_element.get_attribute("src")
                    screenshot_urls.append(url.replace("116x65", "600x338"))
            except NoSuchElementException:
                screenshot_urls = list()

            try:
                review_label_element = driver.find_element_by_css_selector(".user_reviews_filter_options .user_reviews_filter_score .game_review_summary")
                review_label = review_label_element.text
            except NoSuchElementException:
                review_label = None

            try:
                review_total_element = driver.find_element_by_css_selector("label[for=review_type_all] span.user_reviews_count")
                review_total = int(re.sub(r"[\(\),]", "", review_total_element.text))
            except NoSuchElementException:
                review_total = None

            try:
                review_positive_element = driver.find_element_by_css_selector("label[for=review_type_positive] span.user_reviews_count")
                review_positive = int(re.sub(r"[\(\),]", "", review_positive_element.text))
            except NoSuchElementException:
                review_positive = None

            try:
                review_negative_element = driver.find_element_by_css_selector("label[for=review_type_negative] span.user_reviews_count")
                review_negative = int(re.sub(r"[\(\),]", "", review_negative_element.text))
            except NoSuchElementException:
                review_negative = None

            product.set(
                description=description,
                review_label=review_label,
                review_total=review_total,
                review_positive=review_positive,
                review_negative=review_negative
            )

            cls.update_product_tags(product, tags)
            cls.update_product_screenshots(product, screenshot_urls)
            cls.update_product_icons(product)
        except Exception:
            pass
        finally:
            driver.quit()
            display.stop()

    @classmethod
    @db_session
    def update_product_tags(cls, product, tags):
        for tag in tags:
            t = lib.models.ProductTag.get(label=tag)

            if t is None:
                t = lib.models.ProductTag(label=tag)

            if t not in product.product_tags:
                product.product_tags.add(t)

        for tag in product.product_tags:
            if tag.label not in tags:
                product.product_tags.remove(tag)

    @classmethod
    @db_session
    def update_product_screenshots(cls, product, screenshot_urls):
        for screenshot_url in screenshot_urls:
            product_image = lib.models.ProductImage.get(type="screenshot", url=screenshot_url, product=product)

            if product_image is None:
                product_image = lib.models.ProductImage(
                    type="screenshot",
                    url=screenshot_url,
                    product=product
                )

            if product_image not in product.product_images:
                product.product_images.add(product_image)

        for pi in product.product_images:
            if pi.url not in screenshot_urls:
                product.product_images.remove(product_image)

    @classmethod
    @db_session
    def update_product_icons(cls, product):
        small_product_icon = lib.models.ProductImage.get(type="icon_small", product=product)

        if small_product_icon is None:
            lib.models.ProductImage(
                type="icon_small",
                url=f"http://cdn.akamai.steamstatic.com/steam/apps/{product.external_id}/capsule_sm_120.jpg",
                product=product
            )

        large_product_icon = lib.models.ProductImage.get(type="icon_large", product=product)

        if large_product_icon is None:
            lib.models.ProductImage(
                type="icon_large",
                url=f"http://cdn.akamai.steamstatic.com/steam/apps/{product.external_id}/header.jpg",
                product=product
            )

    @classmethod
    @db_session
    def update_product_basic_information(cls, product, data):
        try:
            release_date = datetime_parse(data["release_date"]["date"])
        except Exception as e:
            print(e)
            release_date = product.release_date

        product.set(
            name=data.get("name") or product.name,
            release_date=release_date or product.release_date,
            is_free_to_play=data.get("is_free")
        )

        commit()

    @classmethod
    @db_session
    def update_product_sub_platforms(cls, product, data):
        if "platforms" in data:
            for sub_platform_keyword, is_supported in data["platforms"].items():
                sub_platform = lib.models.SubPlatform.get(lambda sp: sp.name.lower() == sub_platform_keyword)

                if is_supported:
                    if sub_platform not in product.sub_platforms:
                        product.sub_platforms.add(sub_platform)
                else:
                    if sub_platform in product.sub_platforms:
                        product.sub_platforms.remove(sub_platform)

        commit()

    @classmethod
    @db_session
    def update_product_developers(cls, product, data):
        if "developers" in data:
            developers = list()

            for developer_name in data["developers"]:
                developer = lib.models.Developer.get(name=developer_name)

                if developer is None:
                    developer = lib.models.Developer(name=developer_name)

                developers.append(developer)

                if developer not in product.developers:
                    product.developers.add(developer)

            for developer in product.developers:
                if developer not in developers:
                    product.developers.remove(developer)

            commit()

    @classmethod
    @db_session
    def update_product_publishers(cls, product, data):
        if "publishers" in data:
            publishers = list()

            for publisher_name in data["publishers"]:
                publisher = lib.models.Publisher.get(name=publisher_name)

                if publisher is None:
                    publisher = lib.models.Publisher(name=publisher_name)

                publishers.append(publisher)

                if publisher not in product.publishers:
                    product.publishers.add(publisher)

            for publisher in product.publishers:
                if publisher not in publishers:
                    product.publishers.remove(publisher)

            commit()

    @classmethod
    @db_session
    def update_product_genres(cls, product, data):
        if "genres" in data:
            genres = list()

            for genre in data["genres"]:
                g = lib.models.ProductGenre.get(name=genre.get("description"), external_id=str(genre.get("id")))

                if g is None:
                    g = lib.models.ProductGenre(
                        name=genre.get("description"),
                        external_id=str(genre.get("id"))
                    )

                genres.append(g)

                if g not in product.product_genres:
                    product.product_genres.add(g)

            for genre in product.product_genres:
                if genre not in genres:
                    product.product_genres.remove(g)

            commit()

    @classmethod
    @db_session
    def update_product_categories(cls, product, data):
        if "categories" in data:
            categories = list()

            for category in data["categories"]:
                c = lib.models.ProductCategory.get(name=category.get("description"), external_id=str(category.get("id")))

                if c is None:
                    c = lib.models.ProductCategory(
                        name=category.get("description"),
                        external_id=str(category.get("id"))
                   )

                categories.append(c)

                if c not in product.product_categories:
                    product.product_categories.add(c)

            for category in product.product_categories:
                if category not in categories:
                    product.product_categories.remove(c)

            commit()

    @classmethod
    @db_session
    def update_product_parent_children(cls, product, data):
        product_provider = lib.models.ProductProvider.get(name="Steam")

        if "fullgame" in data and data.get("type") == "dlc":
            if data["fullgame"]["appid"] is not None:
                parent_product = lib.models.Product.get(lambda p: p.external_id == data["fullgame"]["appid"] and product_provider in p.product_providers)

                if parent_product is not None:
                    product.parent = parent_product

    @classmethod
    @db_session
    def update_product_achievements(cls, product, json_response):
        if "game" in json_response:
            if "availableGameStats" in json_response["game"]:
                if "achievements" in json_response["game"]["availableGameStats"]:
                    if len(json_response["game"]["availableGameStats"]["achievements"]) > 0:
                        print(f"Steam AppID {product.external_id} has achievements!")

                    achievement_external_ids = []

                    for achievement_data in json_response["game"]["availableGameStats"]["achievements"]:
                        achievement_external_ids.append(achievement_data.get("name"))

                        achievement = lib.models.ProductAchievement.get(product=product, external_id=achievement_data.get("name"))

                        if achievement is None:
                            lib.models.ProductAchievement(
                                name=achievement_data.get("displayName"),
                                external_id=achievement_data.get("name"),
                                description=achievement_data.get("description") or "",
                                is_hidden=bool(achievement_data.get("hidden")),
                                icon_url=achievement_data.get("icongray"),
                                icon_earned_url=achievement_data.get("icon"),
                                product=product
                            )
                        else:
                            achievement.set(
                                name=achievement_data.get("displayName") or achievement.name,
                                external_id=achievement_data.get("name") or achievement.external_id,
                                description=achievement_data.get("description") or achievement.description,
                                is_hidden=bool(achievement_data.get("hidden")),
                                icon_url=achievement_data.get("icongray") or achievement.icon_url,
                                icon_earned_url=achievement_data.get("icon") or achievement.icon_url_earned,
                                updated_at=datetime.utcnow().replace(microsecond=0)
                            )

                            commit()

                    for achievement in product.product_achievements:
                        if achievement.external_id not in achievement_external_ids:
                            product.product_achievements.remove(achievement)
                            achievement.delete()

                            commit()

                    product.set(
                        updated_at=datetime.utcnow().replace(microsecond=0)
                    )

                    commit()

    @classmethod
    @db_session
    def update_achievement_global_percents_from_web_api(cls, product_uuid):
        product = lib.models.Product.get(uuid=uuid.UUID(product_uuid))

        if product is None:
            raise ProductFetcherError("Invalid product provided!")

        requester = RespectfulRequester()
        requester.register_realm("Steam Web API", max_requests=200, timespan=60)

        url = f"{config['product_providers']['steam']['web_api']['base_url']}/ISteamUserStats/GetGlobalAchievementPercentagesForApp/v0002/" \
              f"?gameid={product.external_id}&format=json"

        http_response = requester.get(url, realms=["Steam Web API"], wait=True)

        if http_response.status_code != 200:
            raise ProductFetcherError("Invalid response from the Steam Web API...")

        json_response = http_response.json()

        cls.update_product_achievement_global_percents(product, json_response)

    @classmethod
    @db_session
    def update_product_achievement_global_percents(cls, product, json_response):
        if not len(product.product_achievements):
            return None

        if "achievementpercentages" in json_response:
            if "achievements" in json_response["achievementpercentages"]:
                for achievement_data in json_response["achievementpercentages"]["achievements"]:
                    achievement = lib.models.ProductAchievement.get(product=product, external_id=achievement_data.get("name"))

                    if achievement is None:
                        continue
                    else:
                        achievement.set(
                            global_percent=achievement_data.get("percent"),
                            updated_at=datetime.utcnow().replace(microsecond=0)
                        )

                        commit()

    def _fetch_product_ids(self, product_type="Games", sort_option="Name", max_page=100000):
        url_generator = SteamSearchURLGenerator()

        webdriver = WebDriver("vendor/chromedriver")
        webdriver.set_window_size(1920, 1080)

        page = 1

        product_ids = set()

        while page <= max_page:
            search_url = url_generator.generate(page=page, product_types=[product_type], sort_option=sort_option)
            print(search_url)

            current_product_ids, actual_max_page = self._fetch_ids_for_url(search_url, webdriver)

            if current_product_ids is None:
                continue

            for product_id in current_product_ids:
                product_ids.add(product_id)

            if actual_max_page < max_page:
                max_page = actual_max_page

            page += 1

        webdriver.quit()

        return product_ids

    def _fetch_ids_for_url(self, url=None, webdriver=None):
        webdriver.get(url)

        WebDriverWait(webdriver, 3).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a.search_result_row"))
        )

        try:
            product_ids = []

            for product_link_element in webdriver.find_elements_by_css_selector("a.search_result_row"):
                if "/sub/" not in product_link_element.get_attribute("href"):
                    product_ids.append(product_link_element.get_attribute("data-ds-appid"))
                else:
                    print(f"Skipping bundle located at: {product_link_element.get_attribute('href')}...")

            print("Found %d products..." % len(product_ids))

            # Fetch Max Page
            max_page_element = webdriver.find_elements_by_css_selector("div.search_pagination a")[-2]
            max_page = max_page_element.text

            print("Max Page is: %s" % max_page)

            return product_ids, int(max_page)
        except Exception as e:
            print(e)

            return None, None
