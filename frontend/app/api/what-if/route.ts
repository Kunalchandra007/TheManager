import { NextRequest, NextResponse } from 'next/server';

const backendUrl = process.env.THEMANAGER_API_URL ?? 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const response = await fetch(`${backendUrl}/api/what-if`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: request.headers.get('authorization') ?? '' },
    body: await request.text(),
  });
  return NextResponse.json(await response.json(), { status: response.status });
}
