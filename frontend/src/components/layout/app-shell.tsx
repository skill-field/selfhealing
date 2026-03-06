import { useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Shield, Wifi, WifiOff } from 'lucide-react';
import { Sidebar } from './sidebar';
import { useSSE } from '../../hooks/use-sse';
import { Badge } from '../ui/badge';

export function AppShell() {
  const [collapsed, setCollapsed] = useState(false);
  const { connected } = useSSE();

  return (
    <div className="flex h-screen overflow-hidden bg-gray-950 text-gray-100">
      <Sidebar collapsed={collapsed} onToggle={() => setCollapsed((c) => !c)} />

      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <header className="flex h-14 items-center justify-between border-b border-gray-800 bg-gray-950 px-6">
          <div className="flex items-center gap-3">
            <Shield size={24} className="text-blue-500" />
            <h1 className="text-lg font-bold tracking-tight">Skillfield Sentinel</h1>
            <span className="text-xs text-gray-500">AI Self-Healing Platform</span>
          </div>

          <div className="flex items-center gap-4">
            <Badge variant={connected ? 'success' : 'critical'}>
              {connected ? (
                <span className="flex items-center gap-1.5">
                  <Wifi size={12} /> Connected
                </span>
              ) : (
                <span className="flex items-center gap-1.5">
                  <WifiOff size={12} /> Disconnected
                </span>
              )}
            </Badge>
          </div>
        </header>

        {/* Main content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
