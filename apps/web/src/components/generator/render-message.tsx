'use client';

import type { UseChatHelpers } from '@ai-sdk/react';
import { useEffect } from 'react';
import { toast } from 'sonner';
import { useStickToBottom } from 'use-stick-to-bottom';
import { isAnalysisResult, type AnalysisResult } from '@/lib/ai/analysis-result';
import AnalysisResultCard from './analysis-result-card';
import AiResponse from './text/ai-response';
import UserMessage from './text/user-message';

type PropsType = {
  useChat: UseChatHelpers & {
    addToolResult: ({
      toolCallId,
      result,
    }: {
      toolCallId: string;
      result: unknown;
    }) => void;
  };
  isThinking: boolean;
};

export function RenderMessage({ useChat, isThinking }: PropsType) {
  const { messages, setMessages, reload, error, setInput, data } = useChat;
  const { contentRef, scrollRef } = useStickToBottom();
  const analysisResults: AnalysisResult[] = [];

  for (const item of data ?? []) {
    if (isAnalysisResult(item)) {
      analysisResults.push(item);
    }
  }
  const suggestedPrompts = [
    'Güncel nakit akışı riskini ve sonraki aksiyonları özetle',
    'Hangi pazarlama kampanyaları kârlılığı zorluyor?',
    'Bu şirket için en önemli risk faktörlerini göster',
    'Bu hafta için yönetici seviyesinde CFO özeti hazırla',
  ];

  useEffect(() => {
    if (error?.message.includes('Incorrect API')) {
      toast.error('Incorrect API key provided', {
        description: 'Please check your API key and try again.',
      });
    }
  }, [error]);

  return (
    <div
      className="flex-[1_1_0] overflow-y-auto custom-scrollbar px-5 pt-12 pb-6 md:px-12"
      ref={scrollRef}
    >
      <div
        className="text-gray-800 dark:text-white/90 space-y-6 max-w-none prose dark:prose-invert"
        ref={contentRef}
      >
        {messages.length === 0 && (
          <div className="mx-auto max-w-3xl py-10">
            <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">
              AI CFO Copilot
            </p>
            <h1 className="mt-3 text-3xl font-bold text-gray-900 dark:text-white">
              Nakit akışı, risk ve yönetici finans analizi için soru sor.
            </h1>
            <div className="mt-6 grid gap-3 sm:grid-cols-2">
              {suggestedPrompts.map((prompt) => (
                <button
                  key={prompt}
                  type="button"
                  onClick={() => setInput(prompt)}
                  className="rounded-lg border border-gray-200 bg-white p-4 text-left text-sm font-medium text-gray-700 transition hover:border-primary-200 hover:bg-primary-50/40 dark:border-white/10 dark:bg-white/[0.03] dark:text-white/80 dark:hover:bg-white/[0.06]"
                >
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        )}

        {messages.map((message, messageIdx) => {
          const assistantIndex = messages
            .slice(0, messageIdx + 1)
            .filter((item) => item.role === 'assistant').length - 1;
          const analysisResult =
            message.role === 'assistant'
              ? analysisResults[assistantIndex]
              : undefined;

          return (
            <div key={message.id}>
              {message.parts.map((part, i) => {
                if (part.type === 'text') {
                  if (message.role === 'user') {
                    return (
                      <UserMessage
                        key={`${message.id}-${i}`}
                        message={part.text}
                        showActions={
                          // showActions is true only for the last user message
                          messages.length - 1 === messageIdx ||
                          // if ai responded it should be second to last
                          messages.length - 2 === messageIdx
                        }
                        onEdit={async (newMessage) => {
                          setMessages((prev) => {
                            return prev.map((prevMsg) => {
                              if (prevMsg.id !== message.id) return prevMsg;

                              return {
                                ...prevMsg,
                                parts: prevMsg.parts?.map((part) => ({
                                  ...part,
                                  text: newMessage,
                                })),
                              };
                            });
                          });

                          reload();
                        }}
                      />
                    );
                  }

                  return (
                    <div key={`${message.id}-${i}`}>
                      <AiResponse response={part.text} />
                      {analysisResult && (
                        <AnalysisResultCard result={analysisResult} />
                      )}
                    </div>
                  );
                }
              })}
            </div>
          );
        })}

        {isThinking && (
          <div className="text-gray-500 font-medium">
            AI CFO yanıt hazırlıyor...
          </div>
        )}
      </div>
    </div>
  );
}
