import { getAiCfoBackendBaseUrl } from '@/lib/ai/backend-url';

type DashboardErrorPayload = {
  detail?: unknown;
  message?: unknown;
};

export async function GET(req: Request) {
  const authorization = req.headers.get('authorization');

  if (!authorization?.startsWith('Bearer ')) {
    return Response.json(
      { message: 'Dashboard icin gecerli oturum gerekli.' },
      { status: 401 }
    );
  }

  const backendResponse = await fetch(
    `${getAiCfoBackendBaseUrl()}/dashboard/overview`,
    {
      method: 'GET',
      headers: {
        Authorization: authorization,
      },
      cache: 'no-store',
    }
  );

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
}

function extractErrorMessage(payload: unknown) {
  if (typeof payload === 'string') return payload;

  const errorPayload = payload as DashboardErrorPayload | null;

  if (typeof errorPayload?.detail === 'string') return errorPayload.detail;
  if (typeof errorPayload?.message === 'string') return errorPayload.message;

  return 'Dashboard verisi alinamadi.';
}
