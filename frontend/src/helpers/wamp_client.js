import autobahn from 'autobahn';

import config from '../config.json';

class WAMPClient {
    constructor() {
        if (wampClient === null){
            wampClient = this;
        }

        this.WAMPConnection = null;
        this.WAMPSession = {isOpen: null};

        this.topicSubscriptions = {};

        this.commandQueue = [];
        this.commandQueueInterval = setInterval(() => {
            let commands = this.commandQueue.slice(0);
            this.commandQueue = [];

            commands.forEach((c) => {
               this.execute(c[0], ...c[1]);
            });
        }, 100);


        setTimeout(() => {
            clearInterval(this.commandQueueInterval);
        }, 10000);

        this.connect();

        return wampClient;
    }

    connect() {
        const URL = "ws://" + config.crossbar.host + ":" + config.crossbar.port;

        this.WAMPConnection = new autobahn.Connection({
            url: URL,
            realm: config.crossbar.realm,
            authmethods: ["wampcra"],
            authid: config.crossbar.auth.username,
            onchallenge: this.onChallenge
        });

        this.WAMPConnection.onopen = (session) => {
            this.WAMPSession = session;
        };

        this.WAMPConnection.open();
    }

    execute(functionName, ...args) {
        if (this.WAMPSession.isOpen) {
            this[functionName](...args);
        }
        else {
            this.commandQueue.push([functionName, args]);
        }
    }

    callRPC(endpoint, args, callback) {
        this.WAMPSession.call(endpoint, args).then(
            (result) => {
                callback(true, result);
            },
            (error) => {
                callback(false, error);
            }
        );
    }

    subscribe(topic, handler, match = "exact") {
        this.WAMPSession.subscribe(topic, handler, {match: match}).then(
            (subscription) => {
                this.topicSubscriptions[topic] = subscription;
            },
            (error) => {
                console.error("Topic subscription error: " + error);
            }
        );
    }

    unsubscribe(topic) {
        this.WAMPSession.unsubscribe(this.topicSubscriptions[topic]).then(
            (gone) => {
                delete this.topicSubscriptions[topic];
            },
            (error) =>{
                console.error("Topic unsubscription error: " + error);
            }
        );
    }

    publish(topic, args, kwargs) {
        this.WAMPSession.publish(topic, args, kwargs, {acknowledge: true}).then(
            (publication) => {
                console.debug("Publish Acknowledged: " + publication);
            },
            (error) => {
                console.error("Publish error: " + error);
            }
        )
    }

    onChallenge(session, method, extra) {
        if (method === "wampcra") {
            return autobahn.auth_cra.sign(config.crossbar.auth.password, extra.challenge);
        }
    }
}

export let wampClient = new WAMPClient();