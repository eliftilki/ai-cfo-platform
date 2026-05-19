export const COMPANY_SESSION_STORAGE_KEY = 'ai-cfo-company-session';

export type CompanySession = {
  companyId: string;
  companyName?: string | null;
  email: string;
  accessToken: string;
  refreshToken?: string | null;
  tokenType: string;
};

export function normalizeCompanyId(value: string) {
  return value.trim();
}

export function getStoredCompanySession(): CompanySession | null {
  if (typeof window === 'undefined') return null;

  const rawSession =
    window.localStorage.getItem(COMPANY_SESSION_STORAGE_KEY) ??
    window.sessionStorage.getItem(COMPANY_SESSION_STORAGE_KEY);

  if (!rawSession) return null;

  try {
    const session = JSON.parse(rawSession) as Partial<CompanySession>;

    if (!session.companyId || !session.email || !session.accessToken) {
      return null;
    }

    return {
      companyId: normalizeCompanyId(session.companyId),
      companyName: session.companyName ?? null,
      email: session.email.trim(),
      accessToken: session.accessToken,
      refreshToken: session.refreshToken ?? null,
      tokenType: session.tokenType ?? 'bearer',
    };
  } catch {
    return null;
  }
}

export function storeCompanySession(
  session: CompanySession,
  remember: boolean
) {
  if (typeof window === 'undefined') return;

  const normalizedSession: CompanySession = {
    companyId: normalizeCompanyId(session.companyId),
    companyName: session.companyName ?? null,
    email: session.email.trim(),
    accessToken: session.accessToken,
    refreshToken: session.refreshToken ?? null,
    tokenType: session.tokenType || 'bearer',
  };
  const storage = remember ? window.localStorage : window.sessionStorage;
  const fallbackStorage = remember ? window.sessionStorage : window.localStorage;

  storage.setItem(
    COMPANY_SESSION_STORAGE_KEY,
    JSON.stringify(normalizedSession)
  );
  fallbackStorage.removeItem(COMPANY_SESSION_STORAGE_KEY);
}

export function clearCompanySession() {
  if (typeof window === 'undefined') return;

  window.localStorage.removeItem(COMPANY_SESSION_STORAGE_KEY);
  window.sessionStorage.removeItem(COMPANY_SESSION_STORAGE_KEY);
}
