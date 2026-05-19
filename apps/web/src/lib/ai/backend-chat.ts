import type { JSONValue, UIMessage } from 'ai';
import { createDataStreamResponse, formatDataStreamPart } from 'ai';
import type { AnalysisResult } from './analysis-result';
import { getAiCfoBackendBaseUrl } from './backend-url';

type ChatRequestBody = {
  messages?: UIMessage[];
  access_token?: unknown;
  [key: string]: unknown;
};

type AiCfoAskPayload = {
  question: string;
};

const DATA_STREAM_HEADER = 'x-vercel-ai-data-stream';

export function isBackendChatConfigured(body?: ChatRequestBody) {
  return Boolean(getAccessToken(body));
}

export async function forwardChatToBackend(body: ChatRequestBody) {
  const accessToken = getAccessToken(body);

  if (!accessToken) {
    return new Response('Giriş oturumu yapılandırılmamış', {
      status: 401,
    });
  }

  const payload = toAiCfoAskPayload(body.messages ?? []);
  const backendResponse = await fetch(getAiCfoAskUrl(), {
    method: 'POST',
    headers: buildBackendHeaders(accessToken),
    body: JSON.stringify(payload),
  });

  if (!backendResponse.ok) {
    const errorText = await backendResponse.text();

    return new Response(
      errorText || `Backend request failed with ${backendResponse.status}`,
      { status: backendResponse.status }
    );
  }

  if (isAiSdkDataStream(backendResponse)) {
    return backendResponse;
  }

  const contentType = backendResponse.headers.get('content-type') ?? '';

  if (contentType.includes('application/json')) {
    const data = await backendResponse.json();
    const text = extractTextFromBackendResponse(data);
    const analysisResult = extractAnalysisResult(data);

    return createTextDataStreamResponse(text, analysisResult);
  }

  if (backendResponse.body) {
    return createStreamDataResponse(backendResponse.body);
  }

  return createTextDataStreamResponse(await backendResponse.text());
}

function toAiCfoAskPayload(messages: UIMessage[]): AiCfoAskPayload {
  const question = getMessageText(
    messages.filter((message) => message.role === 'user').at(-1)
  );

  return {
    question,
  };
}

function getMessageText(message?: UIMessage) {
  if (!message) return '';

  return message.parts
    .filter((part) => part.type === 'text')
    .map((part) => part.text)
    .join('\n');
}

function buildBackendHeaders(accessToken: string) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    Authorization: `Bearer ${accessToken}`,
  };

  return headers;
}

function getAiCfoAskUrl() {
  return `${getAiCfoBackendBaseUrl()}/ask`;
}

function getAccessToken(body?: ChatRequestBody) {
  if (typeof body?.access_token === 'string' && body.access_token.trim()) {
    return body.access_token.trim();
  }

  return process.env.CFO_BACKEND_API_KEY?.trim();
}

function isAiSdkDataStream(response: Response) {
  return response.headers.get(DATA_STREAM_HEADER) === 'v1';
}

function createTextDataStreamResponse(
  text: string,
  analysisResult?: AnalysisResult
) {
  return createDataStreamResponse({
    execute(dataStream) {
      if (analysisResult) {
        dataStream.writeData(analysisResult as unknown as JSONValue);
      }

      dataStream.write(formatDataStreamPart('text', text));
    },
  });
}

function createStreamDataResponse(stream: ReadableStream<Uint8Array>) {
  return createDataStreamResponse({
    async execute(dataStream) {
      const reader = stream.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const text = decoder.decode(value, { stream: true });
        if (text) {
          dataStream.write(formatDataStreamPart('text', text));
        }
      }
    },
  });
}

function extractTextFromBackendResponse(data: unknown): string {
  if (typeof data === 'string') return data;

  if (!data || typeof data !== 'object') {
    return '';
  }

  const record = data as Record<string, unknown>;
  const directText =
    firstString(
      record.final_response,
      record.response,
      record.answer,
      record.message,
      record.content,
      record.text
    ) ??
    extractOpenAiChoiceText(record.choices);

  if (directText) return directText;

  if (record.data && typeof record.data === 'object') {
    return extractTextFromBackendResponse(record.data);
  }

  return JSON.stringify(data);
}

function extractAnalysisResult(data: unknown): AnalysisResult | undefined {
  if (!data || typeof data !== 'object') return undefined;

  const record = data as Record<string, unknown>;

  if (
    typeof record.company_id !== 'string' ||
    typeof record.analysis_type !== 'string' ||
    !Array.isArray(record.selected_agents) ||
    !record.sections ||
    typeof record.sections !== 'object'
  ) {
    return undefined;
  }

  return {
    type: 'analysis-result',
    company_id: record.company_id,
    company_name:
      typeof record.company_name === 'string' ? record.company_name : null,
    analysis_type: record.analysis_type as AnalysisResult['analysis_type'],
    selected_agents: record.selected_agents.filter(
      (agent): agent is string => typeof agent === 'string'
    ),
    sections: sanitizeJson(record.sections) as AnalysisResult['sections'],
    agent_run_id:
      typeof record.agent_run_id === 'string' ? record.agent_run_id : null,
  };
}

function sanitizeJson(value: unknown): unknown {
  return JSON.parse(JSON.stringify(value));
}

function firstString(...values: unknown[]) {
  return values.find((value): value is string => typeof value === 'string');
}

function extractOpenAiChoiceText(choices: unknown) {
  if (!Array.isArray(choices)) return undefined;

  const firstChoice = choices[0] as Record<string, unknown> | undefined;
  const message = firstChoice?.message as Record<string, unknown> | undefined;

  return firstString(
    message?.content,
    firstChoice?.text,
    (firstChoice?.delta as Record<string, unknown> | undefined)?.content
  );
}
