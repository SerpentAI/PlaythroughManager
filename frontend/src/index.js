import React from 'react';
import ReactDOM from 'react-dom';

import { BrowserRouter, Route, IndexRoute } from 'react-router-dom'

import { wampClient } from './helpers/wamp_client';

import App from './containers/App';

import './index.css';


ReactDOM.render(
    <BrowserRouter>
        <div>
            <Route path="/" component={App}>

            </Route>
        </div>
    </BrowserRouter>,
    document.getElementById('app')
);
