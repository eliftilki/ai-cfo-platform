'use client';

import { useClickOutside } from '@/hooks/use-click-outside';
import { CloseIcon, MenuIcon } from '@/icons/icons';
import {
  clearCompanySession,
  getStoredCompanySession,
  type CompanySession,
} from '@/lib/company-session';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import DesktopNav from '../layout/header/desktop-nav';
import ThemeToggle from '../layout/header/theme-toggle';

export default function GeneratorHeader({
  toggleSidebar,
  toggleRightSidebar,
  sidebarOpen,
}: {
  toggleSidebar: () => void;
  toggleRightSidebar: () => void;
  sidebarOpen: boolean;
}) {
  const router = useRouter();
  const [companySession, setCompanySession] = useState<CompanySession | null>(
    null
  );
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const accountMenuRef = useClickOutside<HTMLDivElement>(() =>
    setAccountMenuOpen(false)
  );

  useEffect(() => {
    setCompanySession(getStoredCompanySession());
  }, []);

  const accountInitials = useMemo(() => {
    const label =
      companySession?.companyName || companySession?.email || 'AI CFO';

    return label
      .split(/[\s@._-]+/)
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0]?.toUpperCase())
      .join('');
  }, [companySession]);

  const handleLogout = () => {
    clearCompanySession();
    setAccountMenuOpen(false);
    setCompanySession(null);
    router.push('/');
  };

  return (
    <header className="bg-white dark:bg-dark-primary border-b dark:border-gray-800 border-gray-100 sticky top-0 z-50 py-2 lg:py-4">
      <div className="px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 items-center lg:grid-cols-[1fr_auto_1fr]">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center gap-3">
              {/* <!-- Mobile menu button --> */}
              <button
                aria-label="Toggle left sidebar"
                onClick={toggleSidebar}
                className="rounded-md text-gray-400 lg:hidden"
              >
                {sidebarOpen ? (
                  <CloseIcon className="size-6" />
                ) : (
                  <MenuIcon className="size-6" />
                )}
              </button>

              <div className="flex items-center">
                <Link href="/" className="flex items-center gap-2">
                  <span className="text-base font-bold text-gray-900 dark:text-white">
                    AI CFO Platformu
                  </span>
                  <span className="rounded-md bg-primary-500/90 px-1.5 py-0.5 text-xs font-medium text-white">
                    Çalışma Alanı
                  </span>
                </Link>
              </div>
            </div>
          </div>

          <DesktopNav />

          <div className="flex items-center gap-3 justify-self-end">
            <ThemeToggle />

            {companySession && (
              <div ref={accountMenuRef} className="relative">
                <button
                  type="button"
                  onClick={() => setAccountMenuOpen((open) => !open)}
                  className="inline-flex h-11 items-center gap-2 rounded-full border border-gray-200 bg-white py-1.5 pl-1.5 pr-3 text-left transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:bg-dark-primary dark:hover:bg-white/5"
                  aria-expanded={accountMenuOpen}
                  aria-label="Hesap menusu"
                >
                  <span className="inline-flex size-8 items-center justify-center rounded-full bg-primary-500 text-xs font-bold text-white">
                    {accountInitials || 'AI'}
                  </span>
                  <span className="hidden max-w-[180px] sm:block">
                    <span className="block truncate text-sm font-semibold text-gray-800 dark:text-white">
                      {companySession.companyName || companySession.companyId}
                    </span>
                    <span className="block truncate text-xs text-gray-500 dark:text-gray-400">
                      {companySession.email}
                    </span>
                  </span>
                </button>

                {accountMenuOpen && (
                  <div className="absolute right-0 mt-3 w-[280px] rounded-lg border border-gray-200 bg-white p-2 shadow-lg dark:border-white/10 dark:bg-dark-primary">
                    <div className="border-b border-gray-100 px-3 py-3 dark:border-white/10">
                      <p className="truncate text-sm font-semibold text-gray-900 dark:text-white">
                        {companySession.companyName || companySession.companyId}
                      </p>
                      <p className="mt-1 truncate text-xs text-gray-500 dark:text-gray-400">
                        {companySession.email}
                      </p>
                    </div>

                    <div className="py-2">
                      <Link
                        href="/dashboard"
                        onClick={() => setAccountMenuOpen(false)}
                        className="block rounded-md px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                      >
                        Dashboard
                      </Link>
                      <Link
                        href="/text-generator"
                        onClick={() => setAccountMenuOpen(false)}
                        className="block rounded-md px-3 py-2 text-sm font-medium text-gray-600 transition hover:bg-gray-50 hover:text-gray-900 dark:text-gray-300 dark:hover:bg-white/5 dark:hover:text-white"
                      >
                        CFO sohbeti
                      </Link>
                    </div>

                    <button
                      type="button"
                      onClick={handleLogout}
                      className="w-full rounded-md border-t border-gray-100 px-3 py-2 text-left text-sm font-semibold text-red-600 transition hover:bg-red-50 dark:border-white/10 dark:hover:bg-red-500/10"
                    >
                      Cikis yap
                    </button>
                  </div>
                )}
              </div>
            )}

            <button
              onClick={toggleRightSidebar}
              type="button"
              className="inline-flex xl:hidden items-center dark:hover:bg-white/5 dark:hover:text-white/90 hover:bg-gray-100 hover:text-gray-800 text-gray-500 dark:text-gray-400 justify-center border border-gray-200 dark:border-gray-700 rounded-full size-11"
            >
              <span className="sr-only">Sağ paneli aç</span>
              <svg
                className="size-7"
                width="32"
                height="32"
                viewBox="0 0 25 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                transform="rotate(0 0 0)"
              >
                <path
                  d="M6.3125 13.7558C5.346 13.7559 4.5625 12.9723 4.5625 12.0059V11.9959C4.5625 11.0294 5.346 10.2458 6.3125 10.2458C7.279 10.2458 8.0625 11.0294 8.0625 11.9958V12.0058C8.0625 12.9723 7.279 13.7558 6.3125 13.7558Z"
                  fill="currentColor"
                />
                <path
                  d="M18.3125 13.7558C17.346 13.7558 16.5625 12.9723 16.5625 12.0058V11.9958C16.5625 11.0294 17.346 10.2458 18.3125 10.2458C19.279 10.2458 20.0625 11.0294 20.0625 11.9958V12.0058C20.0625 12.9723 19.279 13.7558 18.3125 13.7558Z"
                  fill="currentColor"
                />
                <path
                  d="M10.5625 12.0058C10.5625 12.9723 11.346 13.7558 12.3125 13.7558C13.279 13.7558 14.0625 12.9723 14.0625 12.0058V11.9958C14.0625 11.0294 13.279 10.2458 12.3125 10.2458C11.346 10.2458 10.5625 11.0294 10.5625 11.9958V12.0058Z"
                  fill="currentColor"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    </header>
  );
}
