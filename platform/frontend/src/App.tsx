import { useEffect, useState } from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from './components/AppLayout';
import { DashboardPage } from './pages/Dashboard';
import { AssetsPage } from './pages/Assets';
import { ScanJobsPage } from './pages/ScanJobs';
import { EventsPage } from './pages/Events';
import { EvidenceChainPage } from './pages/EvidenceChain';
import { ReportsPage } from './pages/Reports';
import { SettingsPage } from './pages/Settings';
import { AuditPage } from './pages/Audit';
import { LoginPage } from './pages/Login';
import { RoadmapPage } from './pages/Roadmap';
import { setAuthToken } from './api/client';

export function App() {
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const saved = localStorage.getItem('ics-token');
    if (saved) {
      setAuthToken(saved);
      setToken(saved);
    }
  }, []);

  const handleLogin = (newToken: string) => {
    localStorage.setItem('ics-token', newToken);
    setAuthToken(newToken);
    setToken(newToken);
  };

  if (!token) {
    return <LoginPage onLogin={handleLogin} />;
  }

  return (
    <BrowserRouter>
      <AppLayout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/assets" element={<AssetsPage />} />
          <Route path="/scan-jobs" element={<ScanJobsPage />} />
          <Route path="/events" element={<EventsPage />} />
          <Route path="/audit" element={<AuditPage />} />
          <Route path="/evidence" element={<EvidenceChainPage />} />
          <Route path="/reports" element={<ReportsPage />} />
          <Route path="/roadmap" element={<RoadmapPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </AppLayout>
    </BrowserRouter>
  );
}
