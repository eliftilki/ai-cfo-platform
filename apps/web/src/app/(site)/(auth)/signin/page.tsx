'use client';

import Link from 'next/link';
import { SignInWithGithub, SignInWithGoogle } from '../_components/social-auth';
import SignInForm from './signin-form';

export default function SignInPage() {
  return (
    <section className="relative overflow-hidden py-28">
      <div className="wrapper">
        <div className="relative mx-auto max-w-[600px]">
          <div className="contact-wrapper relative z-30 border border-gray-100 bg-white p-8 dark:border-dark-primary dark:bg-dark-primary sm:p-14">
            <div className="mb-8 text-center">
              <h3 className="mb-2 text-3xl font-bold text-gray-800 dark:text-white/90">
                AI CFO Çalışma Alanı
              </h3>
              <p className="text-gray-500 dark:text-gray-400">
                Analize başlamak için şirket hesabınla giriş yap.
              </p>
            </div>

            <div className="flex flex-col justify-center gap-y-3.5 gap-x-5 sm:flex-row">
              <SignInWithGoogle />
              <SignInWithGithub />
            </div>

            <div className="relative py-3 sm:py-5">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200 dark:border-gray-800" />
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="bg-white p-2 text-gray-400 dark:bg-dark-primary sm:px-5 sm:py-2">
                  veya
                </span>
              </div>
            </div>

            <SignInForm />

            <div className="mt-5">
              <p className="text-sm text-gray-700 dark:text-gray-400">
                Çalışma alanına mı ihtiyacın var?{' '}
                <Link
                  href="/signup"
                  className="text-sm font-semibold text-primary-500"
                >
                  Üye ol
                </Link>
              </p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
