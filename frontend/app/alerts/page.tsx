'use client';

import { useEffect, useState } from 'react';
import { authenticatedFetch } from '@/lib/authenticated-fetch';

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<unknown[]>([]);
  useEffect(() => { authenticatedFetch('/api/alerts').then((response) => response.json()).then(setAlerts).catch(() => setAlerts([])); }, []);
  return <main className="mx-auto max-w-4xl p-8"><h1 className="text-2xl font-bold">Risk Radar Alerts</h1><p className="mt-2 text-muted-foreground">New and worsened risks are shown here after scheduled analysis.</p><p className="mt-6">{alerts.length === 0 ? 'No new alerts.' : `${alerts.length} alerts`}</p></main>;
}
