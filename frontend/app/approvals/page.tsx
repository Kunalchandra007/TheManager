'use client';

import { useEffect, useState } from 'react';

type Action = { action_id: string; status: string; draft_email: string; evidence?: Array<{ title: string; url: string }> };

export default function ApprovalsPage() {
  const [actions, setActions] = useState<Action[]>([]);
  useEffect(() => { fetch('/api/actions').then((response) => response.json()).then(setActions).catch(() => setActions([])); }, []);
  return <main className="mx-auto max-w-4xl p-8"><h1 className="text-2xl font-bold">Approvals</h1><p className="mt-2 text-muted-foreground">Supplier communications remain pending until a human reviews and approves them.</p><div className="mt-6 space-y-4">{actions.length === 0 ? <p>No pending actions.</p> : actions.map((action) => <article className="rounded border p-4" key={action.action_id}><p className="font-semibold">{action.status}</p><pre className="mt-2 whitespace-pre-wrap text-sm">{action.draft_email}</pre></article>)}</div></main>;
}
