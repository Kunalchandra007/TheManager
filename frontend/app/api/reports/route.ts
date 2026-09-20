import { NextResponse } from 'next/server';

export async function GET() {
  try {
    const backendUrl = process.env.THEMANAGER_API_URL ?? 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/reports`);
    const data = await response.json();
    console.log(data);

    return NextResponse.json({ reports: data }, { status: 200 });
  } catch (error) {
    console.error('Error fetching reports:', error);
    return NextResponse.json({ error: 'Failed to fetch reports' }, { status: 500 });
  }
}
