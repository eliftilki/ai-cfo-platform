export const navItems = [
  {
    type: 'link',
    href: '/',
    label: 'Genel Bakış',
  },
  {
    type: 'link',
    label: 'AI CFO Sohbeti',
    href: '/text-generator',
  },
  {
    type: 'link',
    label: 'Planlar',
    href: '/pricing',
  },
  {
    type: 'link',
    label: 'İletişim',
    href: '/contact',
  },
  {
    type: 'dropdown',
    label: 'Hesap',
    items: [
      { href: '/signin', label: 'Giriş Yap' },
      { href: '/signup', label: 'Üye Ol' },
      { href: '/reset-password', label: 'Şifre Sıfırla' },
      { href: '/not-found', label: '404 Hatası' },
    ],
  },
] satisfies NavItem[];

type NavItem = Record<string, string | unknown> &
  (
    | {
        type: 'link';
        href: string;
      }
    | {
        type: 'dropdown';
      }
  );
