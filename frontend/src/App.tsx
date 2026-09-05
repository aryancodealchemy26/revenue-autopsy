import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { LandingPage } from './pages/LandingPage';
import { AppLayout } from './components/layout/AppLayout';
import { OverviewPage } from './pages/OverviewPage';
import { IncidentsPage } from './pages/IncidentsPage';
import { IncidentDetailPage } from './pages/IncidentDetailPage';
import { ActionsPage } from './pages/ActionsPage';
import { OutcomesPage } from './pages/OutcomesPage';
import { PoliciesPage } from './pages/PoliciesPage';
import { AuditTrailPage } from './pages/AuditTrailPage';
import { RevenueHealthPage } from './pages/RevenueHealthPage';
import { IntegrationsPage } from './pages/IntegrationsPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Marketing & Product Flow */}
        <Route path="/" element={<LandingPage />} />

        {/* Operational Workspace */}
        <Route path="/app" element={<AppLayout />}>
          <Route index element={<Navigate to="/app/overview" replace />} />
          <Route path="overview" element={<OverviewPage />} />
          <Route path="health" element={<RevenueHealthPage />} />
          <Route path="incidents" element={<IncidentsPage />} />
          <Route path="incidents/:id" element={<IncidentDetailPage />} />
          <Route path="actions" element={<ActionsPage />} />
          <Route path="outcomes" element={<OutcomesPage />} />
          <Route path="policies" element={<PoliciesPage />} />
          <Route path="audit-trail" element={<AuditTrailPage />} />
          <Route path="integrations" element={<IntegrationsPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Fallback */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
