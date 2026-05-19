import { getCurrentYear } from '@/lib/utils';
import Link from 'next/link';

const links = [
  { href: '/text-generator', label: 'AI CFO Sohbeti' },
  { href: '/pricing', label: 'Planlar' },
  { href: '/privacy', label: 'Gizlilik' },
  { href: '/contact', label: 'İletişim' },
];

export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-gray-950 dark:border-gray-800">
      <div className="wrapper flex flex-col gap-6 py-8 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-bold text-white">AI CFO Platformu</p>
          <p className="mt-2 max-w-[520px] text-sm text-gray-400">
            Kimlik doğrulamalı şirket çalışma alanları, agent analizleri ve CFO
            seviyesinde kararlar için finans zekası.
          </p>
        </div>

        <nav className="flex flex-wrap gap-4">
          {links.map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="text-sm font-medium text-gray-400 transition hover:text-white"
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>

      <div className="border-t border-white/10 py-4">
        <div className="wrapper text-sm text-gray-500">
          &copy; {getCurrentYear()} AI CFO Platformu. Tüm hakları saklıdır.
        </div>
      </div>
    </footer>
  );
}
