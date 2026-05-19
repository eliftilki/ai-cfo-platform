import { AI_MODEL } from '@/lib/ai/model';
import {
  forwardChatToBackend,
  isBackendChatConfigured,
} from '@/lib/ai/backend-chat';
import { PROMPT } from '@/lib/ai/prompts';
import { errorHandler, getMostRecentUserMessage } from '@/lib/utils';
import { createIdGenerator, streamText } from 'ai';

export const maxDuration = 50;

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const { messages } = body;

    if (!Array.isArray(messages)) {
      return new Response('Invalid messages payload', {
        status: 400,
      });
    }

    const userMessage = getMostRecentUserMessage(messages);

    if (!userMessage) {
      return new Response('No user message found', {
        status: 404,
      });
    }

    if (isBackendChatConfigured(body)) {
      return forwardChatToBackend(body);
    }

    const result = streamText({
      model: AI_MODEL,
      system: PROMPT,
      messages,
      experimental_generateMessageId: createIdGenerator({
        prefix: 'msgs',
      }),
    });

    return result.toDataStreamResponse({
      getErrorMessage:
        process.env.NODE_ENV === 'development' ? errorHandler : undefined,
    });
  } catch (error) {
    console.log(error);

    return new Response(errorHandler(error), {
      status: 500,
    });
  }
}
