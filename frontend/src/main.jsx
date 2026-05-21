import React from 'react';
import ReactDOM from 'react-dom/client';
import { HashRouter } from 'react-router-dom';
import { SessionProvider } from './state/SessionContext.jsx';
import { SitesProvider } from './state/SitesContext.jsx';
import AppRouter from './router/AppRouter.jsx';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <HashRouter>
      <SessionProvider>
        <SitesProvider>
          <AppRouter />
        </SitesProvider>
      </SessionProvider>
    </HashRouter>
  </React.StrictMode>
);
