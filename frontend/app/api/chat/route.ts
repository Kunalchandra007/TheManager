import { NextResponse } from 'next/server';

export async function POST(request: Request) {
  try {
    const body = await request.json();
    const { message, session_id } = body;

    if (!message) {
      return NextResponse.json(
        {
          status: 'error',
          response: null,
          error: 'Message is required',
          session_id: null,
        },
        { status: 400 }
      );
    }

    const backendUrl = process.env.THEMANAGER_API_URL ?? 'http://localhost:8000';
    const response = await fetch(`${backendUrl}/api/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: request.headers.get('authorization') ?? '',
      },
      body: JSON.stringify({
        message,
        session_id: session_id || undefined,
      }),
    });

    const responseText = await response.text();
    let data: unknown;

    try {
      data = JSON.parse(responseText);
    } catch {
      return NextResponse.json(
        {
          status: 'error',
          response: null,
          error: `Backend returned invalid JSON (HTTP ${response.status})`,
          session_id: null,
        },
        { status: response.status }
      );
    }

    if (!response.ok) {
      return NextResponse.json(data, { status: response.status });
    }

    if (!data || typeof data !== 'object' || Array.isArray(data)) {
      return NextResponse.json(
        {
          status: 'error',
          response: null,
          error: `Backend returned an unexpected response (HTTP ${response.status})`,
          session_id: null,
        },
        { status: response.status }
      );
    }

    const responseData = data as { response?: string; session_id?: string };

    return NextResponse.json({
      status: 'success',
      response: responseData.response || '',
      error: null,
      session_id: responseData.session_id || null,
    });
  } catch (error) {
    return NextResponse.json(
      {
        status: 'error',
        response: null,
        error: error instanceof Error ? error.message : 'An error occurred',
        session_id: null,
      },
      { status: 500 }
    );
  }
}
