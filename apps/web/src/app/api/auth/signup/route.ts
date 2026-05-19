import { getAiCfoBackendBaseUrl } from '@/lib/ai/backend-url';

type SignupErrorPayload = {
  detail?: unknown;
  message?: unknown;
};

export async function POST(req: Request) {
  let body: unknown;

  try {
    body = await req.json();
  } catch {
    return Response.json(
      { message: 'Gecersiz uyelik istegi.' },
      { status: 400 }
    );
  }

  try {
    const backendResponse = await fetch(`${getAiCfoBackendBaseUrl()}/auth/signup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const contentType = backendResponse.headers.get('content-type') ?? '';
    const responseBody = contentType.includes('application/json')
      ? await backendResponse.json()
      : await backendResponse.text();

    if (!backendResponse.ok) {
      return Response.json(
        {
          message: extractErrorMessage(responseBody),
        },
        { status: backendResponse.status }
      );
    }

    return Response.json(responseBody);
  } catch {
    return Response.json(
      {
        message:
          'Backend baglantisi kurulamadi. API servisinin calistigini kontrol et.',
      },
      { status: 503 }
    );
  }
}

function extractErrorMessage(payload: unknown) {
  if (typeof payload === 'string') return payload;

  const errorPayload = payload as SignupErrorPayload | null;

  if (typeof errorPayload?.detail === 'string') return errorPayload.detail;
  if (typeof errorPayload?.message === 'string') return errorPayload.message;

  return 'Uyelik olusturulamadi. Lutfen bilgilerini kontrol et.';
}
