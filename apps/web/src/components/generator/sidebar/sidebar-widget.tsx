'use client';

import { getStoredCompanySession } from '@/lib/company-session';
import { getCurrentYear } from '@/lib/utils';
import { useEffect, useState } from 'react';

export default function SidebarWidget() {
  const [workspace, setWorkspace] = useState({
    name: 'AI CFO Çalışma Alanı',
    email: 'Giriş yapılmadı',
  });

  useEffect(() => {
    const session = getStoredCompanySession();

    if (!session) return;

    setWorkspace({
      name: session.companyName || session.companyId,
      email: session.email,
    });
  }, []);

  return (
    <div>
      <div className="pt-5 pb-3 px-3 rounded-2xl widget-bg">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium text-gray-800 dark:text-white/90">
              {workspace.name}
            </p>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {workspace.email}
            </p>
          </div>

          <span className="bg-white dark:bg-white/10 text-[#344054] dark:text-white/70 px-2 py-0.5 text-xs font-medium rounded-full">
            CFO
          </span>
        </div>
        <div className="mt-5">
          <button className="rounded-full gradient-btn text-white flex gap-2 items-center justify-center text-xs font-semibold w-full px-6 py-3">
            Risk aksiyonlarını incele
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="18"
              height="18"
              viewBox="0 0 18 18"
              fill="none"
            >
              <path
                d="M9.61054 2.0625L3.58887 10.5264H8.38943L8.38943 15.9375L14.4111 7.47361L9.61054 7.47361V2.0625Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>
      <div className="mt-3 px-3 text-center tracking-wide text-xs text-gray-400">
        &copy; {getCurrentYear()} AI CFO Platform
      </div>
    </div>
  );
}
