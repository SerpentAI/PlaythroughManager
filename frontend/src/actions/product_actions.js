import {wampClient} from '../helpers/wamp_client';

import AppDispatcher from '../dispatcher/dispatcher';

import config from '../config.json';


function fetchProduct(productProvider, productName) {
    const args = [productProvider, productName];

    function onFetchProduct(success, response) {
        if (success) {
            AppDispatcher.dispatch({
                actionType: "PRODUCT_FETCHED",
                body: response
            });
        }
        else {
            AppDispatcher.dispatch({
                actionType: "PRODUCT_FETCH_ERROR",
                body: response
            });
        }
    }

    wampClient.callRPC(config.crossbar.realm + ".fetch_product", args, onFetchProduct);
}

function fetchProductNames() {
    const args = [];

    function onFetchProductNames(success, response) {
        if (success) {
            AppDispatcher.dispatch({
                actionType: "PRODUCT_NAMES_FETCHED",
                body: response
            });
        }
        else {
            AppDispatcher.dispatch({
                actionType: "PRODUCT_NAMES_FETCH_ERROR",
                body: response
            });
        }
    }

    wampClient.execute("callRPC", config.crossbar.realm + ".fetch_select_products", args, onFetchProductNames);
}

export {fetchProduct, fetchProductNames}
