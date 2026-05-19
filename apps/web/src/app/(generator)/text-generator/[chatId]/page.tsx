'use client';

import GeneratorInput from '@/components/generator/generator-input';
import { RenderMessage } from '@/components/generator/render-message';
import { GradientBlob } from '@/components/gradient-blob';
import {
  clearCompanySession,
  getStoredCompanySession,
  type CompanySession,
} from '@/lib/company-session';
import { useChat } from '@ai-sdk/react';
import { createIdGenerator } from 'ai';
import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

export default function Page() {
  const router = useRouter();
  const [isThinking, setIsThinking] = useState(false);
  const [companySession, setCompanySession] = useState<CompanySession | null>(
    null
  );

  const chatHandler = useChat({
    generateId: createIdGenerator({ prefix: 'msgc' }),
    sendExtraMessageFields: true,
    onResponse: () => setIsThinking(false),
    onError: () => setIsThinking(false),
  });

  useEffect(() => {
    const session = getStoredCompanySession();

    if (!session) {
      router.replace('/signin?next=/text-generator');
      return;
    }

    setCompanySession(session);
  }, [router]);

  const handleWorkspaceSwitch = () => {
    clearCompanySession();
    router.push('/signin?next=/text-generator');
  };

  return (
    <div className="contents">
      <RenderMessage useChat={chatHandler} isThinking={isThinking} />

      <div className="px-5 md:px-12">
        {companySession && (
          <div className="mb-3 flex flex-wrap items-center justify-between gap-3 rounded-lg border border-gray-200 bg-white px-4 py-3 text-sm text-gray-600 shadow-theme-xs dark:border-white/10 dark:bg-white/[0.03] dark:text-white/70">
            <span>
              Çalışma alanı:{' '}
              <strong className="font-semibold text-gray-800 dark:text-white">
                {companySession.companyName || companySession.companyId}
              </strong>
            </span>
            <button
              type="button"
              onClick={handleWorkspaceSwitch}
              className="font-medium text-primary-500 hover:text-primary-600"
            >
              Çalışma alanını değiştir
            </button>
          </div>
        )}

        <form
          onSubmit={(e) => {
            if (!companySession) {
              e.preventDefault();
              router.replace('/signin?next=/text-generator');
              return;
            }

            setIsThinking(true);
            chatHandler.handleSubmit(e, {
              body: {
                access_token: companySession.accessToken,
              },
            });
          }}
        >
          <GeneratorInput
            value={chatHandler.input}
            onChange={chatHandler.handleInputChange}
            disabled={!companySession}
          />
        </form>

        <GradientBlob />
      </div>
    </div>
  );
}
