import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { ROUTES } from './routes.js';
import { RequireRole } from './guards.jsx';
import { useSession } from '../state/SessionContext.jsx';

import App from '../App.jsx';
import OverviewPage          from '../modules/bd/overview/OverviewPage.jsx';
import DraftsPage            from '../modules/bd/drafts/DraftsPage.jsx';
import ShortlistPage         from '../modules/bd/shortlist/ShortlistPage.jsx';
import ExecStagingPage       from '../modules/staging/exec/ExecStagingPage.jsx';
import SupervisorStagingPage from '../modules/staging/supervisor/SupervisorStagingPage.jsx';
import ArchivePage           from '../modules/archive/ArchivePage.jsx';
import AddDetailsPage        from '../modules/loi/details/AddDetailsPage.jsx';

// App is used as a layout shell (renders TopBar + Sidebar + <Outlet/>).
// Page components are nested routes rendered into the Outlet.

export default function AppRouter() {
  return (
    <Routes>
      <Route element={<App/>}>
        <Route index                  element={<OverviewPage/>}/>
        <Route path={ROUTES.PIPELINE}  element={<DraftsPage/>}/>
        <Route path={ROUTES.SHORTLIST} element={<ShortlistPage/>}/>

        <Route path={ROUTES.STAGING_EXEC} element={
          <RequireRole roles={['exec']}>
            <ExecStagingPage/>
          </RequireRole>
        }/>
        <Route path={ROUTES.STAGING_SUPERVISOR} element={
          <RequireRole roles={['supervisor', 'sub_supervisor']}>
            <SupervisorStagingPage/>
          </RequireRole>
        }/>
        {/* Generic /staging redirects based on role */}
        <Route path={ROUTES.STAGING} element={<StagingRedirect/>}/>

        <Route path={ROUTES.ARCHIVE} element={
          <RequireRole roles={['supervisor', 'sub_supervisor']}>
            <ArchivePage/>
          </RequireRole>
        }/>

        {/* Sub-path routes for shortlist details / timeline — rendered as full pages */}
        <Route path={ROUTES.ADD_DETAILS}   element={<ShortlistPage/>}/>
        <Route path={ROUTES.LOI_TIMELINE}  element={<ShortlistPage/>}/>

        <Route path="*" element={<Navigate to={ROUTES.OVERVIEW} replace/>}/>
      </Route>
    </Routes>
  );
}

function StagingRedirect() {
  const { role } = useSession();
  return <Navigate to={role === 'exec' ? ROUTES.STAGING_EXEC : ROUTES.STAGING_SUPERVISOR} replace/>;
}
