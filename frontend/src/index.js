import React from 'react';
import ReactDOM from 'react-dom';

import { BrowserRouter as Router, Route, IndexRoute } from 'react-router-dom'

import { wampClient } from './helpers/wamp_client';

import App from './containers/App';

import './index.css';


ReactDOM.render(
    <Router>
        <div>
            <Route path="/" component={App} />
        </div>
    </Router>,
    document.getElementById('app')
);
