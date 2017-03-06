import invoke
from invoke import task

from pony.orm import *
import lib.models

from lib.helpers.steam.steam_search_url_generator import SteamSearchURLGenerator

from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from pyvirtualdisplay import Display


# TODO: Make game provider agnostic...

@task
def discover_all(ctx, product_type="Games"):
    product_ids = fetch_all_ids(product_type=product_type, sort_option="Name")

    #for product_id in product_ids:
        #discovered_product(product_type=product_type, product_id=product_id)


@task
def discover_recent(ctx, product_type="Games", max_page=1):
    #product_ids = fetch_recent_ids(product_type=product_type, max_page=max_page)

    #for product_id in product_ids:
    #    discovered_product(product_type=product_type, product_id=product_id)
    pass


def fetch_all_ids(product_type="Games", sort_option="Name"):
    url_generator = SteamSearchURLGenerator()

    display = Display(visible=0, size=(1920, 1080,))
    display.start()

    driver = webdriver.Chrome("vendor/chromedriver")
    driver.set_window_size(1920, 1080)

    page = 1
    max_page = 1

    product_ids = set()

    while page <= max_page:
        search_url = url_generator.generate(page=page, product_types=[product_type], sort_option=sort_option)
        print(search_url)

        current_product_ids, actual_max_page = fetch_ids_for_url(search_url, driver)

        if current_product_ids is None:
            continue

        for product_id in current_product_ids:
            product_ids.add(int(product_id))

        if max_page == 1:
            max_page = actual_max_page

        page += 1

    driver.quit()

    print(len(product_ids))
    print(product_ids)

    return product_ids


def fetch_ids_for_url(url=None, driver=None):
    driver.get(url)

    WebDriverWait(driver, 3).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "a.search_result_row"))
    )

    try:
        product_ids = []

        # Fetch Product IDs
        for product_link_element in driver.find_elements_by_css_selector("a.search_result_row"):
            if "/sub/" not in product_link_element.get_attribute("href"):
                product_ids.append(int(product_link_element.get_attribute("data-ds-appid")))
            else:
                print(f"Skipping bundle located at: {product_link_element.get_attribute('href')}...")

        print("Found %d products..." % len(product_ids))

        # Fetch Max Page
        max_page_element = driver.find_elements_by_css_selector("div.search_pagination a")[-2]
        max_page = max_page_element.text

        print("Max Page is: %s" % max_page)

        return product_ids, int(max_page)
    except Exception as e:
        print(e)

        return None, None


namespace = invoke.Collection("product_fetching")

namespace.add_task(discover_all)
namespace.add_task(discover_recent)
