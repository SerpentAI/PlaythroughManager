import React, { Component, PropTypes } from 'react';

import { Tag, Intent} from '@blueprintjs/core';

import './index.css';


class ProductRecord extends Component {
    constructor(props, context) {
        super(props, context);

        this.state = {

        };
    }

    static propTypes = {
        product: PropTypes.object.isRequired
    };

    componentDidMount() {
        console.log(this.props)
    }

    componentWillUnmount() {

    }

    render() {
        return (
            <section id="product_record"  style={{marginTop: 30}}>

                <div className="pt-callout pt-intent-primary">
                    <h5>{this.props.product.name}</h5>
                    {this.getDeveloperNames().join(", ")} - {this.getPublisherNames().join(", ")}
                </div>

                <div>
                    <img
                        className="pt-card pt-elevation-2 pt-interactive"
                        style={{padding: 2}}
                        src={this.getLargeProductIconURL()}
                        alt={this.props.product.name + " Image"}
                    />

                    <div style={{marginTop: 10}}>
                        {this.getProductCategoryNames().map((pc) => {
                            return(
                                <Tag key={"PC-" + pc} intent={Intent.SUCCESS} style={{marginRight: 5}}>{pc}</Tag>
                            )
                        })}
                    </div>
                </div>
            </section>
        );
    }

    getDeveloperNames = () => {
        let developers = [];

        Object.keys(this.props.product.developers).forEach((k) => {
            developers.push(this.props.product.developers[k].name);
        });

        return developers;
    };

    getPublisherNames = () => {
        let publishers = [];

        Object.keys(this.props.product.publishers).forEach((k) => {
            publishers.push(this.props.product.publishers[k].name);
        });

        return publishers;
    };

    getProductCategoryNames = () => {
        let categories = [];

        Object.keys(this.props.product.product_categories).forEach((k) => {
            categories.push(this.props.product.product_categories[k].name);
        });

        return categories;
    };

    getLargeProductIconURL = () => {
        let largeProductIcon = this.props.product.product_images.icon_large[0];
        return largeProductIcon.url;
    }
}

export default ProductRecord;
