import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/app-shell';
import { DashboardPage } from './components/dashboard/dashboard-page';
import { WatchPage } from './components/errors/watch-page';
import { ThinkPage } from './components/errors/think-page';
import { HealPage } from './components/fixes/heal-page';
import { VerifyPage } from './components/deployments/verify-page';
import { EvolvePage } from './components/features/evolve-page';
import { AuditPage } from './components/audit/audit-page';
import { PresentationPage } from './components/presentation/presentation-page';
import { ReposPage } from './components/settings/repos-page';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route index element={<DashboardPage />} />
          <Route path="watch" element={<WatchPage />} />
          <Route path="think" element={<ThinkPage />} />
          <Route path="heal" element={<HealPage />} />
          <Route path="verify" element={<VerifyPage />} />
          <Route path="evolve" element={<EvolvePage />} />
          <Route path="audit" element={<AuditPage />} />
          <Route path="presentation" element={<PresentationPage />} />
          <Route path="settings" element={<ReposPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
