import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const backendUrl = process.env.THEMANAGER_API_URL ?? 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/thinking-log-ids`, {
      headers: { Authorization: request.headers.get('authorization') ?? '' },
    });
    const data = await response.json();

    return NextResponse.json({
      status: 'success',
      sessions: data,
      error: null,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        sessions: null,
        error: error instanceof Error ? error.message : 'An error occurred',
      },
      { status: 500 }
    );
  }
}
