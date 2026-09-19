import { NextRequest, NextResponse } from 'next/server';

const backendUrl = process.env.THEMANAGER_API_URL ?? 'http://localhost:8000';

export async function GET(request: NextRequest) {
  const response = await fetch(`${backendUrl}/api/alerts`, { headers: { Authorization: request.headers.get('authorization') ?? '' } });
  return NextResponse.json(await response.json(), { status: response.status });
}
