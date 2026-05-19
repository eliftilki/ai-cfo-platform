'use client';

import {
  getStoredCompanySession,
  type CompanySession,
} from '@/lib/company-session';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import type React from 'react';
import { useCallback, useEffect, useMemo, useState } from 'react';

type DashboardOverview = {
  company: {
    id: string;
    name?: string | null;
  };
  period: {
    cashflow_days: number;
    marketing_days: number;
  };
  refresh_status: 'fresh' | 'stale' | 'generated_on_demand' | 'missing';
  generated_at?: string | null;
  expires_at?: string | null;
  is_stale: boolean;
  data_freshness: Record<string, string | null>;
  summary_cards: {
    net_cashflow_30d?: number | null;
    income_30d?: number | null;
    expense_30d?: number | null;
    liquidity_risk?: string | null;
    overall_roas?: number | null;
    overall_cac?: number | null;
    marketing_risk?: string | null;
    overall_risk_score?: number | null;
    overall_risk_level?: string | null;
    unread_alert_count?: number | null;
    critical_alert_count?: number | null;
  };
  cashflow: {
    metrics?: {
      income?: number | null;
      expense?: number | null;
      net_cashflow?: number | null;
      liquidity_risk?: string | null;
      transaction_count?: number | null;
    };
    top_expense_categories?: Array<{ category?: string; amount?: number }>;
    top_income_categories?: Array<{ category?: string; amount?: number }>;
    transaction_count?: number | null;
  };
  marketing: {
    metrics?: {
      total_spend?: number | null;
      total_attributed_revenue?: number | null;
      overall_roas?: number | null;
      overall_cac?: number | null;
      total_conversions?: number | null;
      marketing_risk?: string | null;
      low_roas_campaign_count?: number | null;
    };
    platform_summary?: Array<{
      platform?: string;
      spend?: number;
      revenue?: number;
      roas?: number;
      cac?: number;
      conversions?: number;
    }>;
    low_roas_campaigns?: Array<{
      campaign_name?: string | null;
      platform?: string;
      roas?: number;
      ad_spend?: number;
      attributed_revenue?: number;
      cac?: number;
    }>;
    campaign_count?: number | null;
  };
  risk: {
    latest_score?: {
      overall_risk_score?: number | null;
      risk_level?: string | null;
      score_date?: string | null;
    } | null;
    top_risk_factors?: string[];
    priority_actions?: string[];
  };
  alerts: {
    unread_count?: number | null;
    critical_count?: number | null;
    latest?: Array<{
      id?: string;
      alert_type?: string | null;
      severity?: string | null;
      title?: string | null;
      message?: string | null;
      is_read?: boolean | null;
      created_at?: string | null;
    }>;
  };
};

type SummaryCard = {
  label: string;
  value: string;
  helper: string;
  tone: string;
};

const numberFormatter = new Intl.NumberFormat('tr-TR');
const moneyFormatter = new Intl.NumberFormat('tr-TR', {
  maximumFractionDigits: 0,
  style: 'currency',
  currency: 'TRY',
});

const agents = [
  'CFO Agent',
  'Cashflow Agent',
  'Risk Agent',
  'Marketing Agent',
];

export default function DashboardPage() {
  const router = useRouter();
  const [companySession, setCompanySession] = useState<CompanySession | null>(
    null
  );
  const [overview, setOverview] = useState<DashboardOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchDashboard = useCallback(async (session: CompanySession) => {
    setIsLoading(true);
    setErrorMessage(null);

    try {
      const response = await fetch('/api/dashboard/overview', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${session.accessToken}`,
        },
        cache: 'no-store',
      });

      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.message || 'Dashboard verisi alinamadi.');
      }

      setOverview(payload as DashboardOverview);
    } catch (error) {
      setErrorMessage(
        error instanceof Error ? error.message : 'Dashboard verisi alinamadi.'
      );
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const session = getStoredCompanySession();

    if (!session) {
      router.replace('/signin?next=/dashboard');
      return;
    }

    setCompanySession(session);
    void fetchDashboard(session);
  }, [fetchDashboard, router]);

  const summaryCards = useMemo(
    () => buildSummaryCards(overview),
    [overview]
  );

  if (!companySession) {
    return (
      <main className="flex min-h-full items-center justify-center px-5 py-12">
        <p className="text-sm font-medium text-gray-500 dark:text-gray-400">
          Calisma alani hazirlaniyor...
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-full bg-gray-50 px-5 py-8 text-gray-800 dark:bg-dark-secondary dark:text-white/90 md:px-8 lg:px-10">
      <div className="mx-auto max-w-7xl">
        <section className="flex flex-col gap-5 border-b border-gray-200 pb-6 dark:border-white/10 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="flex flex-wrap items-center gap-3">
              <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">
                Dashboard
              </p>
              {overview && (
                <span className="rounded-full bg-white px-3 py-1 text-xs font-semibold text-gray-500 ring-1 ring-gray-200 dark:bg-white/5 dark:text-gray-300 dark:ring-white/10">
                  {getRefreshLabel(overview.refresh_status, overview.is_stale)}
                </span>
              )}
            </div>
            <h1 className="mt-2 text-3xl font-bold text-gray-900 dark:text-white">
              Hos geldin,{' '}
              {overview?.company.name ||
                companySession.companyName ||
                companySession.companyId}
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-gray-500 dark:text-gray-400">
              {overview
                ? `${overview.period.cashflow_days} gunluk nakit akisi ve ${overview.period.marketing_days} gunluk pazarlama performansi backend snapshot verisinden guncellendi.`
                : 'Finans ozetleri, agent sinyalleri ve CFO sohbeti icin ana calisma alanin burada.'}
            </p>
          </div>

          <div className="flex flex-col gap-3 sm:flex-row">
            <button
              type="button"
              onClick={() => fetchDashboard(companySession)}
              disabled={isLoading}
              className="inline-flex h-11 items-center justify-center rounded-full border border-gray-200 px-5 text-sm font-semibold text-gray-700 transition hover:border-gray-300 hover:bg-white disabled:cursor-not-allowed disabled:opacity-60 dark:border-white/10 dark:text-gray-300 dark:hover:bg-white/5"
            >
              {isLoading ? 'Yenileniyor...' : 'Veriyi yenile'}
            </button>
            <Link
              href="/text-generator"
              className="inline-flex h-11 items-center justify-center rounded-full bg-primary-500 px-5 text-sm font-semibold text-white transition hover:bg-primary-600"
            >
              CFO sohbetini ac
            </Link>
          </div>
        </section>

        {errorMessage && (
          <section className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-500/20 dark:bg-red-500/10 dark:text-red-300">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <p>{errorMessage}</p>
              <button
                type="button"
                onClick={() => fetchDashboard(companySession)}
                className="w-fit rounded-full bg-white px-4 py-2 text-sm font-semibold text-red-700 ring-1 ring-red-200 transition hover:bg-red-100 dark:bg-transparent dark:text-red-300 dark:ring-red-500/30 dark:hover:bg-red-500/10"
              >
                Tekrar dene
              </button>
            </div>
          </section>
        )}

        <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          {(isLoading && !overview ? getLoadingCards() : summaryCards).map(
            (card) => (
              <article
                key={card.label}
                className="rounded-lg border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-white/10 dark:bg-white/[0.03]"
              >
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  {card.label}
                </p>
                <p className={`mt-3 text-3xl font-bold ${card.tone}`}>
                  {card.value}
                </p>
                <p className="mt-2 text-sm text-gray-500 dark:text-gray-400">
                  {card.helper}
                </p>
              </article>
            )
          )}
        </section>

        <section className="mt-6 grid gap-6 xl:grid-cols-[1fr_380px]">
          <div className="space-y-6">
            <DashboardPanel
              title="Nakit akisi"
              description="Gelir, gider ve kategori dagilimi."
            >
              <MetricGrid
                items={[
                  {
                    label: 'Gelir',
                    value: formatMoney(overview?.cashflow.metrics?.income),
                  },
                  {
                    label: 'Gider',
                    value: formatMoney(overview?.cashflow.metrics?.expense),
                  },
                  {
                    label: 'Net nakit',
                    value: formatMoney(
                      overview?.cashflow.metrics?.net_cashflow
                    ),
                  },
                  {
                    label: 'Islem',
                    value: formatNumber(
                      overview?.cashflow.transaction_count ??
                        overview?.cashflow.metrics?.transaction_count
                    ),
                  },
                ]}
              />

              <CategoryList
                title="En yuksek gider kategorileri"
                rows={overview?.cashflow.top_expense_categories}
              />
            </DashboardPanel>

            <DashboardPanel
              title="Pazarlama performansi"
              description="ROAS, CAC ve platform bazli performans."
            >
              <MetricGrid
                items={[
                  {
                    label: 'Harcamalar',
                    value: formatMoney(
                      overview?.marketing.metrics?.total_spend
                    ),
                  },
                  {
                    label: 'Gelir',
                    value: formatMoney(
                      overview?.marketing.metrics?.total_attributed_revenue
                    ),
                  },
                  {
                    label: 'ROAS',
                    value: formatDecimal(
                      overview?.marketing.metrics?.overall_roas
                    ),
                  },
                  {
                    label: 'CAC',
                    value: formatMoney(overview?.marketing.metrics?.overall_cac),
                  },
                ]}
              />

              <PlatformList rows={overview?.marketing.platform_summary} />
            </DashboardPanel>
          </div>

          <aside className="space-y-6">
            <DashboardPanel
              title="Risk ve uyarilar"
              description="Son risk skoru ve okunmamis uyarilar."
            >
              <div className="rounded-md bg-gray-50 p-4 dark:bg-white/[0.04]">
                <p className="text-sm text-gray-500 dark:text-gray-400">
                  Genel risk skoru
                </p>
                <p className="mt-2 text-3xl font-bold text-amber-600">
                  {formatNullable(overview?.risk.latest_score?.overall_risk_score)}
                </p>
                <p className="mt-1 text-sm font-medium text-gray-600 dark:text-gray-300">
                  {riskLabel(overview?.risk.latest_score?.risk_level)}
                </p>
              </div>

              <AlertList rows={overview?.alerts.latest} />
            </DashboardPanel>

            <DashboardPanel
              title="Aktif agentlar"
              description="Dashboard verisini kullanan analiz ekipleri."
            >
              <div className="space-y-3">
                {agents.map((agent) => (
                  <div
                    key={agent}
                    className="flex items-center justify-between rounded-md border border-gray-100 px-3 py-3 dark:border-white/10"
                  >
                    <span className="text-sm font-medium">{agent}</span>
                    <span className="text-xs font-semibold text-emerald-600">
                      Hazir
                    </span>
                  </div>
                ))}
              </div>
            </DashboardPanel>

            <DashboardPanel title="Veri tazeligi">
              <FreshnessList overview={overview} email={companySession.email} />
            </DashboardPanel>
          </aside>
        </section>
      </div>
    </main>
  );
}

function DashboardPanel({
  title,
  description,
  children,
}: {
  title: string;
  description?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="rounded-lg border border-gray-200 bg-white p-5 shadow-theme-xs dark:border-white/10 dark:bg-white/[0.03]">
      <div>
        <h2 className="text-xl font-bold text-gray-900 dark:text-white">
          {title}
        </h2>
        {description && (
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {description}
          </p>
        )}
      </div>
      <div className="mt-5">{children}</div>
    </section>
  );
}

function MetricGrid({
  items,
}: {
  items: Array<{ label: string; value: string }>;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-md border border-gray-100 p-3 dark:border-white/10"
        >
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {item.label}
          </p>
          <p className="mt-1 text-lg font-bold text-gray-900 dark:text-white">
            {item.value}
          </p>
        </div>
      ))}
    </div>
  );
}

function CategoryList({
  title,
  rows,
}: {
  title: string;
  rows?: Array<{ category?: string; amount?: number }>;
}) {
  if (!rows?.length) {
    return <EmptyState text="Kategori verisi henuz yok." />;
  }

  return (
    <div className="mt-5">
      <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
        {title}
      </h3>
      <div className="mt-3 space-y-2">
        {rows.map((row) => (
          <div
            key={row.category}
            className="flex items-center justify-between rounded-md bg-gray-50 px-3 py-2 dark:bg-white/[0.04]"
          >
            <span className="text-sm text-gray-600 dark:text-gray-300">
              {row.category || 'uncategorized'}
            </span>
            <span className="text-sm font-semibold text-gray-900 dark:text-white">
              {formatMoney(row.amount)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function PlatformList({
  rows,
}: {
  rows?: DashboardOverview['marketing']['platform_summary'];
}) {
  if (!rows?.length) {
    return <EmptyState text="Platform performansi henuz yok." />;
  }

  return (
    <div className="mt-5 space-y-2">
      {rows.slice(0, 5).map((row) => (
        <div
          key={row.platform}
          className="grid gap-2 rounded-md bg-gray-50 px-3 py-3 text-sm dark:bg-white/[0.04] sm:grid-cols-[1fr_auto_auto]"
        >
          <span className="font-semibold text-gray-900 dark:text-white">
            {row.platform || 'unknown'}
          </span>
          <span className="text-gray-500 dark:text-gray-400">
            ROAS {formatDecimal(row.roas)}
          </span>
          <span className="text-gray-500 dark:text-gray-400">
            {formatMoney(row.spend)}
          </span>
        </div>
      ))}
    </div>
  );
}

function AlertList({
  rows,
}: {
  rows?: DashboardOverview['alerts']['latest'];
}) {
  if (!rows?.length) {
    return <EmptyState text="Aktif uyari bulunmuyor." />;
  }

  return (
    <div className="mt-4 space-y-3">
      {rows.slice(0, 5).map((alert) => (
        <article
          key={alert.id || alert.title}
          className="rounded-md border border-gray-100 p-3 dark:border-white/10"
        >
          <div className="flex items-start justify-between gap-3">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white">
              {alert.title || 'Uyari'}
            </h3>
            <span className="rounded-full bg-gray-100 px-2 py-1 text-xs font-semibold text-gray-600 dark:bg-white/10 dark:text-gray-300">
              {riskLabel(alert.severity)}
            </span>
          </div>
          {alert.message && (
            <p className="mt-2 text-sm leading-6 text-gray-500 dark:text-gray-400">
              {alert.message}
            </p>
          )}
        </article>
      ))}
    </div>
  );
}

function FreshnessList({
  overview,
  email,
}: {
  overview: DashboardOverview | null;
  email: string;
}) {
  const rows = [
    ['Oturum', email],
    ['Snapshot', formatDate(overview?.generated_at)],
    ['Nakit verisi', formatDate(overview?.data_freshness.cashflow_data_last_seen_at)],
    [
      'Pazarlama verisi',
      formatDate(overview?.data_freshness.marketing_data_last_seen_at),
    ],
    ['Risk verisi', formatDate(overview?.data_freshness.risk_score_last_seen_at)],
    ['Uyari verisi', formatDate(overview?.data_freshness.alerts_last_seen_at)],
  ];

  return (
    <div className="space-y-3">
      {rows.map(([label, value]) => (
        <div key={label} className="text-sm">
          <p className="font-semibold text-gray-900 dark:text-white">{label}</p>
          <p className="mt-1 break-all text-gray-500 dark:text-gray-400">
            {value}
          </p>
        </div>
      ))}
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <div className="rounded-md border border-dashed border-gray-200 p-4 text-sm text-gray-500 dark:border-white/10 dark:text-gray-400">
      {text}
    </div>
  );
}

function buildSummaryCards(overview: DashboardOverview | null): SummaryCard[] {
  const cards = overview?.summary_cards;

  return [
    {
      label: 'Net nakit akisi',
      value: formatMoney(cards?.net_cashflow_30d),
      helper: `Likidite riski: ${riskLabel(cards?.liquidity_risk)}`,
      tone: getAmountTone(cards?.net_cashflow_30d),
    },
    {
      label: 'ROAS',
      value: formatDecimal(cards?.overall_roas),
      helper: `Pazarlama riski: ${riskLabel(cards?.marketing_risk)}`,
      tone: 'text-sky-600',
    },
    {
      label: 'Risk skoru',
      value: formatNullable(cards?.overall_risk_score),
      helper: `Risk seviyesi: ${riskLabel(cards?.overall_risk_level)}`,
      tone: 'text-amber-600',
    },
    {
      label: 'Uyarilar',
      value: formatNumber(cards?.unread_alert_count),
      helper: `${formatNumber(cards?.critical_alert_count)} kritik uyari`,
      tone: 'text-red-600',
    },
  ];
}

function getLoadingCards(): SummaryCard[] {
  return ['Net nakit akisi', 'ROAS', 'Risk skoru', 'Uyarilar'].map((label) => ({
    label,
    value: '...',
    helper: 'Veri yukleniyor',
    tone: 'text-gray-400',
  }));
}

function formatMoney(value?: number | null) {
  if (typeof value !== 'number') return '-';
  return moneyFormatter.format(value);
}

function formatNumber(value?: number | null) {
  if (typeof value !== 'number') return '0';
  return numberFormatter.format(value);
}

function formatDecimal(value?: number | null) {
  if (typeof value !== 'number') return '-';
  return numberFormatter.format(Number(value.toFixed(2)));
}

function formatNullable(value?: number | string | null) {
  if (typeof value === 'number') return numberFormatter.format(value);
  if (typeof value === 'string' && value.trim()) return value;
  return '-';
}

function formatDate(value?: string | null) {
  if (!value) return '-';

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '-';

  return new Intl.DateTimeFormat('tr-TR', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(date);
}

function riskLabel(value?: string | null) {
  const labels: Record<string, string> = {
    low: 'Dusuk',
    medium: 'Orta',
    high: 'Yuksek',
    critical: 'Kritik',
    fresh: 'Guncel',
    stale: 'Bayat',
  };

  if (!value) return '-';
  return labels[value] || value;
}

function getRefreshLabel(status: DashboardOverview['refresh_status'], stale: boolean) {
  if (stale) return 'Bayat veri';

  const labels: Record<DashboardOverview['refresh_status'], string> = {
    fresh: 'Guncel',
    stale: 'Bayat',
    generated_on_demand: 'Yeni uretildi',
    missing: 'Eksik',
  };

  return labels[status];
}

function getAmountTone(value?: number | null) {
  if (typeof value !== 'number') return 'text-gray-500';
  return value >= 0 ? 'text-emerald-600' : 'text-red-600';
}
