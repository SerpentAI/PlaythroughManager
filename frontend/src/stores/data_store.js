import AppDispatcher from '../dispatcher/dispatcher';
import EventEmitter from 'events';

let _data = {};

let DataStore = Object.assign({}, EventEmitter.prototype, {
    getDataByKey: function(key) {
        return _data[key];
    },

    setDataKey: function(key, value) {
        _data[key] = value;
    },

    clearData: function() {
        _data = {};
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

DataStore.setMaxListeners(1000);

AppDispatcher.register(function(payload) {
    const action = payload.actionType;

    switch(action) {
        case "PRODUCT_NAMES_FETCHED":
            DataStore.setDataKey("productNames", payload.body.product_names);
            DataStore.emitChange("PRODUCT_NAMES_FETCHED");
            break;
        default: // Nothing
    }
});

export default DataStore;