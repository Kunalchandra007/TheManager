'use client';

import { useState } from 'react';

type Result = { before: { percentage: number; flag: string }; after: { percentage: number; flag: string } };

export default function WhatIfPage() {
  const [delayDays, setDelayDays] = useState(10);
  const [result, setResult] = useState<Result | null>(null);

  async function simulate() {
    const response = await fetch('/api/what-if', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ equipment_id: 1, days_variance: 4, days_until_due: 100, delay_days: delayDays }) });
    setResult(await response.json());
  }

  return <main className="mx-auto max-w-2xl p-8"><h1 className="text-2xl font-bold">What-If Simulator</h1><p className="mt-2 text-muted-foreground">Simulate a deterministic port or supplier delay using the existing risk formula.</p><label className="mt-6 block">Delay days<input className="ml-3 border p-2" type="number" min="0" value={delayDays} onChange={(event) => setDelayDays(Number(event.target.value))} /></label><button className="mt-4 rounded bg-primary px-4 py-2 text-primary-foreground" onClick={simulate}>Simulate impact</button>{result && <section className="mt-6 rounded border p-4"><p>Before: {result.before.percentage}% — {result.before.flag}</p><p>After: {result.after.percentage}% — {result.after.flag}</p></section>}</main>;
}
