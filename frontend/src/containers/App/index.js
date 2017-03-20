import React, { Component, PropTypes } from 'react';

import {Button, Intent} from '@blueprintjs/core';

import ProductRecord from '../../components/ProductRecord';

import * as ProductActions from '../../actions/product_actions';

import ProductStore from '../../stores/product_store';
import DataStore from '../../stores/data_store';


class App extends Component {
    constructor(props, context) {
        super(props, context);

        this.state = {
            product: null,
            productName: "",
            productNames: []
        };
    }

    componentDidMount() {
        ProductActions.fetchProductNames();

        ProductStore.addChangeListener("PRODUCT_FETCHED", this._onProductFetched);
        DataStore.addChangeListener("PRODUCT_NAMES_FETCHED", this._onProductNamesFetched);
    };

    componentWillUnmount() {
        ProductStore.removeChangeListener("PRODUCT_FETCHED", this._onProductFetched);
        DataStore.removeChangeListener("PRODUCT_NAMES_FETCHED", this._onProductNamesFetched);
    };

    render() {
        return (
            <section id="App">
                <h1>Playthrough Manager</h1>

                <Button intent={Intent.SUCCESS} iconName="search" className="pt-large" onClick={this.handleFetchProductClick}>Fetch Product</Button>

                <div className="pt-select">
                    <select onChange={this.handleProductNameChange}>
                        <option>Select a Product...</option>
                        {this.state.productNames.map((pn) => {
                            return(
                                <option value={pn}>{pn}</option>
                            )
                        })}
                    </select>
                </div>

                <input
                    type="text"
                    className="pt-input pt-large"
                    placeholder="Product Name"
                    value={this.state.productName}
                    style={{marginLeft: 10}}
                    onChange={this.handleProductNameChange}
                />


                {this.state.product !== null ? this.renderProductRecord() : ""}
            </section>
        )
    }

    renderProductRecord() {
        return (
            <ProductRecord product={this.state.product} />
        )
    }

    handleFetchProductClick = (e) => {
        const productProvider = "Steam";

        ProductActions.fetchProduct(productProvider, this.state.productName);
    };

    handleProductNameChange = (e) => {
        this.setState({productName: e.currentTarget.value})
    };

    _onProductFetched = () => {
        let product = ProductStore.getProduct();
        this.setState({product: product});
    };

    _onProductNamesFetched = () => {
        let productNames = DataStore.getDataByKey("productNames");
        this.setState({productNames: productNames});
    }
}

export default App;