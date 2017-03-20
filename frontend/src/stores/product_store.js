import AppDispatcher from '../dispatcher/dispatcher';
import EventEmitter from 'events';

let _product = {};
let _errors = [];


let ProductStore = Object.assign({}, EventEmitter.prototype, {
    getProduct: function() {
        return _product;
    },

    getErrors: function() {
        return _errors;
    },

    setProduct: function(product) {
        _product = product;
    },

    setErrors: function(errors) {
        _errors = errors;
    },

    clearProduct: function() {
        _product = {};
    },

    clearErrors: function() {
        _errors = {};
    },

    emitChange: function(event) {
        this.emit(event);
    },

    addChangeListener: function(event, callback) {
        this.on(event, callback);
    },

    removeChangeListener: function(event, callback) {
        this.removeListener(event, callback);
    }
});

ProductStore.setMaxListeners(1000);

AppDispatcher.register(function(payload) {
    const action = payload.actionType;

    switch(action) {
        case "PRODUCT_FETCHED":
            ProductStore.setProduct(payload.body.product);
            ProductStore.emitChange("PRODUCT_FETCHED");
            break;
        default: // Nothing
    }
});

export default ProductStore;