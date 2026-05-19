'use client';

import type { AnalysisResult, AnalysisSection } from '@/lib/ai/analysis-result';

type Props = {
  result: AnalysisResult;
};

type InsightCard = {
  label: string;
  value: string;
  tone?: 'default' | 'good' | 'warning' | 'danger';
};

const moduleLabels: Record<string, string> = {
  cashflow_agent: 'Nakit akışı analizi',
  marketing_agent: 'Pazarlama verimliliği',
  risk_prioritization_engine: 'Risk önceliklendirme',
  cfo_response_generator: 'Yönetici sentezi',
};

const analysisLabels: Record<string, string> = {
  domain_cashflow: 'Nakit akışı analizi',
  domain_marketing: 'Pazarlama analizi',
  synthesis_risk: 'Risk sentezi',
  executive_summary: 'Yönetici özeti',
  unknown: 'Analiz sonucu',
};

const flagLabels: Record<string, string> = {
  negative_30d_cashflow: 'Son 30 günde negatif net nakit akışı',
  negative_7d_cashflow: 'Son 7 günde negatif net nakit akışı',
  expense_pressure: 'Gider baskısı yüksek',
  liquidity_pressure: 'Likidite baskısı var',
  concentrated_outflows: 'Nakit çıkışları belirli giderlerde yoğunlaşıyor',
  cashflow_data_unavailable: 'Nakit akışı verisi bulunamadı',
  cashflow_limited_data_coverage: 'Nakit akışı veri kapsamı sınırlı',
  cashflow_low_confidence: 'Nakit akışı analiz güveni sınırlı',
  low_marketing_efficiency: 'Reklam verimliliği düşük',
  low_roas_campaigns: 'Düşük ROAS kampanyalar var',
  multiple_low_roas_campaigns: 'Çok sayıda düşük ROAS kampanyası var',
  marketing_spend_risk: 'Pazarlama harcaması risk yaratıyor',
  marketing_data_unavailable: 'Pazarlama verisi bulunamadı',
  marketing_limited_data_coverage: 'Pazarlama veri kapsamı sınırlı',
  marketing_low_confidence: 'Pazarlama analiz güveni sınırlı',
  data_quality_warning: 'Veri kalitesi uyarısı',
};

const metricLabels: Record<string, string> = {
  income_7d: '7 gün gelir',
  expense_7d: '7 gün gider',
  net_cashflow_7d: '7 gün net nakit akışı',
  income_14d: '14 gün gelir',
  expense_14d: '14 gün gider',
  net_cashflow_14d: '14 gün net nakit akışı',
  income_30d: '30 gün gelir',
  expense_30d: '30 gün gider',
  net_cashflow_30d: '30 gün net nakit akışı',
  liquidity_risk: 'Likidite riski',
  campaign_count: 'Kampanya sayısı',
  total_spend: 'Toplam harcama',
  total_attributed_revenue: 'Atfedilen gelir',
  overall_roas: 'ROAS',
  overall_cac: 'CAC',
  total_clicks: 'Tıklama',
  total_impressions: 'Gösterim',
  total_conversions: 'Dönüşüm',
  overall_risk_score: 'Risk skoru',
  overall_risk_level: 'Risk seviyesi',
  cashflow_component: 'Nakit akışı bileşeni',
  marketing_component: 'Pazarlama bileşeni',
  stored_component: 'Kayıtlı risk bileşeni',
  recommendation_count: 'Öneri sayısı',
  has_cashflow_context: 'Nakit akışı bağlamı',
  has_marketing_context: 'Pazarlama bağlamı',
  has_risk_context: 'Risk bağlamı',
};

const riskLabels: Record<string, string> = {
  low: 'Düşük',
  medium: 'Orta',
  high: 'Yüksek',
  critical: 'Kritik',
  dusuk: 'Düşük',
  düşük: 'Düşük',
  orta: 'Orta',
  yuksek: 'Yüksek',
  yüksek: 'Yüksek',
  kritik: 'Kritik',
};

const moneyKeys = [
  'income',
  'expense',
  'cashflow',
  'spend',
  'revenue',
  'cac',
  'settlement',
  'payment',
];

export default function AnalysisResultCard({ result }: Props) {
  const sections = result.sections || {};
  const dataNote = buildDataNote(sections);

  return (
    <div className="mt-4 max-w-4xl space-y-4 rounded-lg border border-gray-200 bg-white p-4 shadow-theme-xs dark:border-white/10 dark:bg-white/[0.04]">
      <div className="border-b border-gray-100 pb-4 dark:border-white/10">
        <p className="text-xs font-semibold uppercase tracking-wide text-primary-500">
          Analiz dayanağı
        </p>
        <h3 className="mt-1 text-lg font-bold text-gray-900 dark:text-white">
          {analysisLabels[result.analysis_type] || 'Analiz sonucu'}
        </h3>
        <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
          {result.company_name || result.company_id}
        </p>
        {dataNote && (
          <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-800 dark:bg-amber-500/10 dark:text-amber-200">
            {dataNote}
          </p>
        )}
      </div>

      <section>
        <h4 className="text-sm font-semibold text-gray-800 dark:text-white/90">
          Kullanılan analiz modülleri
        </h4>
        <div className="mt-3 flex flex-wrap gap-2">
          {result.selected_agents.map((agent) => (
            <span
              key={agent}
              className="rounded-full bg-emerald-50 px-3 py-1 text-xs font-semibold text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-300"
            >
              {moduleLabels[agent] || humanize(agent)}
            </span>
          ))}
        </div>
      </section>

      <div className="grid gap-4 lg:grid-cols-2">
        {sections.cashflow && (
          <InsightSection
            title="Nakit akışı"
            section={sections.cashflow}
            cards={buildCashflowCards(sections.cashflow)}
            signalKeys={['negative_30d_cashflow', 'expense_pressure', 'liquidity_pressure', 'concentrated_outflows']}
          />
        )}
        {sections.marketing && (
          <InsightSection
            title="Pazarlama"
            section={sections.marketing}
            cards={buildMarketingCards(sections.marketing)}
            signalKeys={['low_marketing_efficiency', 'low_roas_campaigns', 'multiple_low_roas_campaigns', 'marketing_spend_risk']}
          />
        )}
        {sections.risk && (
          <InsightSection
            title="Risk"
            section={sections.risk}
            cards={buildRiskCards(sections.risk)}
            signalKeys={['negative_30d_cashflow', 'expense_pressure', 'liquidity_pressure', 'marketing_limited_data_coverage', 'data_quality_warning']}
            actionsTitle="Risk azaltıcı aksiyonlar"
          />
        )}
        {sections.cfo && <CfoSection section={sections.cfo} />}
      </div>
    </div>
  );
}

function InsightSection({
  title,
  section,
  cards,
  signalKeys,
  actionsTitle = 'Öncelikli aksiyonlar',
}: {
  title: string;
  section: AnalysisSection;
  cards: InsightCard[];
  signalKeys: string[];
  actionsTitle?: string;
}) {
  const flags = getList(section.flags);
  const riskFactors = getList(section.top_risk_factors);
  const actions = getList(section.priority_actions || section.final_recommendations);
  const signals = uniqueKnownLabels([...flags, ...riskFactors], signalKeys);

  return (
    <section className="rounded-lg border border-gray-100 p-4 dark:border-white/10">
      <h4 className="text-sm font-bold uppercase tracking-wide text-gray-700 dark:text-white/80">
        {title}
      </h4>

      <div className="mt-4 grid gap-3 sm:grid-cols-2">
        {cards.map((card) => (
          <MetricCard key={`${title}-${card.label}`} card={card} />
        ))}
      </div>

      {signals.length > 0 && <List title="Ana sinyaller" items={signals} />}
      {actions.length > 0 && (
        <List title={actionsTitle} items={actions.map(formatAction)} />
      )}
    </section>
  );
}

function CfoSection({ section }: { section: AnalysisSection }) {
  const metrics = getRecord(section.metrics);
  const confidence = getNumber(section.confidence);
  const dataCoverage = getRecord(section.data_coverage);
  const errors = getList(section.errors);
  const recommendations = getList(section.final_recommendations);
  const cards: InsightCard[] = [
    {
      label: 'Güven düzeyi',
      value: confidenceLabel(confidence),
      tone: confidence !== undefined && confidence < 0.7 ? 'warning' : 'good',
    },
    {
      label: 'Öneri sayısı',
      value: formatValue(metrics?.recommendation_count ?? recommendations.length),
    },
    {
      label: 'Veri kapsamı',
      value: dataCoverageLabel(dataCoverage),
      tone: errors.length > 0 ? 'warning' : 'default',
    },
  ];

  return (
    <section className="rounded-lg border border-gray-100 p-4 dark:border-white/10">
      <h4 className="text-sm font-bold uppercase tracking-wide text-gray-700 dark:text-white/80">
        Yönetici sentezi
      </h4>
      <p className="mt-3 text-sm leading-6 text-gray-600 dark:text-gray-300">
        Ana CFO cevabı yukarıdaki mesajda verildi. Bu bölüm, cevabın hangi veri güveni ve kapsamla üretildiğini özetler.
      </p>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        {cards.map((card) => (
          <MetricCard key={`cfo-${card.label}`} card={card} />
        ))}
      </div>
      {errors.length > 0 && (
        <List title="Veri notları" items={errors.map(formatFlag)} />
      )}
    </section>
  );
}

function MetricCard({ card }: { card: InsightCard }) {
  const toneClass =
    card.tone === 'danger'
      ? 'text-red-700 dark:text-red-300'
      : card.tone === 'warning'
        ? 'text-amber-700 dark:text-amber-300'
        : card.tone === 'good'
          ? 'text-emerald-700 dark:text-emerald-300'
          : 'text-gray-900 dark:text-white';

  return (
    <div className="rounded-md bg-gray-50 px-3 py-2 dark:bg-white/[0.04]">
      <p className="text-xs text-gray-500 dark:text-gray-400">{card.label}</p>
      <p className={`mt-1 break-words text-sm font-semibold ${toneClass}`}>
        {card.value}
      </p>
    </div>
  );
}

function buildCashflowCards(section: AnalysisSection): InsightCard[] {
  const metrics = getRecord(section.metrics) || {};
  const net30 = getNumber(metrics.net_cashflow_30d);
  const expense30 = getNumber(metrics.expense_30d);
  const income30 = getNumber(metrics.income_30d);
  const risk = normalizeRisk(metrics.liquidity_risk);

  return [
    {
      label: '30 gün net nakit akışı',
      value: formatMetric('net_cashflow_30d', net30),
      tone: net30 !== undefined && net30 < 0 ? 'danger' : 'good',
    },
    {
      label: 'Likidite riski',
      value: risk || '-',
      tone: riskTone(risk),
    },
    {
      label: '30 gün gelir',
      value: formatMetric('income_30d', income30),
    },
    {
      label: '30 gün gider',
      value: formatMetric('expense_30d', expense30),
      tone: expense30 !== undefined && income30 !== undefined && expense30 > income30 ? 'warning' : 'default',
    },
  ];
}

function buildMarketingCards(section: AnalysisSection): InsightCard[] {
  const metrics = getRecord(section.metrics) || {};
  const roas = getNumber(metrics.overall_roas);
  const spend = getNumber(metrics.total_spend);
  const revenue = getNumber(metrics.total_attributed_revenue);
  const risk = normalizeRisk(metrics.marketing_risk);

  return [
    {
      label: 'ROAS',
      value: formatMetric('overall_roas', roas),
      tone: roas !== undefined && roas < 1.5 ? 'warning' : 'good',
    },
    {
      label: 'Toplam harcama',
      value: formatMetric('total_spend', spend),
    },
    {
      label: 'Atfedilen gelir',
      value: formatMetric('total_attributed_revenue', revenue),
    },
    {
      label: 'Pazarlama riski',
      value: risk || inferMarketingRisk(roas),
      tone: riskTone(risk || inferMarketingRisk(roas)),
    },
  ];
}

function buildRiskCards(section: AnalysisSection): InsightCard[] {
  const metrics = getRecord(section.metrics) || getRecord(section.assessment) || {};
  const score = getNumber(metrics.overall_risk_score);
  const level = normalizeRisk(metrics.overall_risk_level);

  return [
    {
      label: 'Risk skoru',
      value: score !== undefined ? `${score}/100` : '-',
      tone: score !== undefined && score >= 50 ? 'danger' : 'good',
    },
    {
      label: 'Risk seviyesi',
      value: level || '-',
      tone: riskTone(level),
    },
    {
      label: 'Nakit etkisi',
      value: formatValue(metrics.cashflow_component),
      tone: getNumber(metrics.cashflow_component) !== undefined && Number(metrics.cashflow_component) >= 50 ? 'danger' : 'default',
    },
    {
      label: 'Pazarlama etkisi',
      value: formatValue(metrics.marketing_component),
      tone: getNumber(metrics.marketing_component) !== undefined && Number(metrics.marketing_component) >= 50 ? 'warning' : 'default',
    },
  ];
}

function uniqueKnownLabels(items: unknown[], preferredKeys: string[]) {
  const all = items.map(formatFlag).filter(Boolean);
  const preferred = preferredKeys
    .map((key) => all.find((item) => item === formatFlag(key)))
    .filter((item): item is string => Boolean(item));
  const rest = all.filter((item) => !preferred.includes(item));
  return Array.from(new Set([...preferred, ...rest])).slice(0, 5);
}

function buildDataNote(sections: Record<string, AnalysisSection>) {
  const allErrors = Object.values(sections).flatMap((section) =>
    getList(section.errors).map(formatFlag)
  );
  const coverageNotes = Object.values(sections).flatMap((section) =>
    coverageNotesFrom(section.data_coverage)
  );
  const notes = Array.from(new Set([...coverageNotes, ...allErrors]));

  if (notes.length === 0) return undefined;
  return `Not: ${notes.slice(0, 2).join(' ')} Bu nedenle sonuçlar kesin hüküm değil, yönetim önceliği olarak okunmalıdır.`;
}

function coverageNotesFrom(value: unknown): string[] {
  const record = getRecord(value);
  if (!record) return [];

  const direct = getString(record.data_coverage_note);
  const nested = Object.values(record).flatMap((item) => coverageNotesFrom(item));
  return [direct, ...nested].filter((item): item is string => Boolean(item));
}

function dataCoverageLabel(dataCoverage?: Record<string, unknown>) {
  if (!dataCoverage) return 'Standart kapsam';
  const notes = coverageNotesFrom(dataCoverage);
  if (notes.length > 0) return 'Sınırlı veri kapsamı';
  return 'Standart kapsam';
}

function confidenceLabel(value?: number) {
  if (value === undefined) return 'Belirtilmedi';
  if (value >= 0.85) return 'Yüksek';
  if (value >= 0.7) return 'Orta';
  return 'Sınırlı';
}

function formatMetric(key: string, value: unknown) {
  if (value == null) return '-';
  const number = getNumber(value);
  if (number === undefined) return formatValue(value);

  if (key.includes('roas')) return number.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
  if (key.includes('cac')) return formatCurrency(number);
  if (moneyKeys.some((part) => key.toLowerCase().includes(part))) {
    return formatCurrency(number);
  }

  return number.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
}

function formatCurrency(value: number) {
  return `${value.toLocaleString('tr-TR', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  })} TL`;
}

function formatFlag(value: unknown): string {
  if (typeof value !== 'string') return formatValue(value);
  return flagLabels[value] || normalizeRisk(value) || humanize(value);
}

function formatAction(value: unknown): string {
  if (typeof value !== 'string') return formatValue(value);
  return value
    .replace('Protect liquidity first by linking marketing spend increases to measurable cash recovery.', 'Bugün: Pazarlama bütçesi artışlarını ölçülebilir nakit toparlanması görülene kadar durdurun.')
    .replace('Freeze or reschedule non-critical cash outflows for the next 30 days.', 'Bugün: Kritik olmayan nakit çıkışlarını dondurun veya önümüzdeki 30 gün için yeniden takvimlendirin.')
    .replace('Review the largest expense categories and set weekly payment priorities.', 'Bugün: En büyük gider kategorilerini gözden geçirip haftalık ödeme önceliklerini belirleyin.')
    .replace('Pause or reduce budget on low-ROAS campaigns and reallocate spend to efficient channels.', 'Bu hafta: Düşük ROAS kampanyalarında bütçeyi azaltıp harcamayı daha verimli kanallara kaydırın.');
}

function normalizeRisk(value: unknown): string | undefined {
  if (typeof value !== 'string') return undefined;
  return riskLabels[value.trim().toLowerCase()];
}

function riskTone(value?: string): InsightCard['tone'] {
  if (value === 'Kritik' || value === 'Yüksek') return 'danger';
  if (value === 'Orta') return 'warning';
  if (value === 'Düşük') return 'good';
  return 'default';
}

function inferMarketingRisk(roas?: number) {
  if (roas === undefined) return '-';
  if (roas < 1.2) return 'Yüksek';
  if (roas < 1.5) return 'Orta';
  return 'Düşük';
}

function List({ title, items }: { title: string; items: unknown[] }) {
  return (
    <div className="mt-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-gray-500 dark:text-gray-400">
        {title}
      </p>
      <ul className="mt-2 space-y-2">
        {items.slice(0, 5).map((item, index) => (
          <li
            key={`${title}-${index}`}
            className="rounded-md border border-gray-100 px-3 py-2 text-sm text-gray-600 dark:border-white/10 dark:text-gray-300"
          >
            {formatValue(item)}
          </li>
        ))}
      </ul>
    </div>
  );
}

function getString(value: unknown) {
  return typeof value === 'string' && value.trim() ? value : undefined;
}

function getNumber(value: unknown) {
  if (typeof value === 'number' && Number.isFinite(value)) return value;
  if (typeof value === 'string' && value.trim() && Number.isFinite(Number(value))) {
    return Number(value);
  }
  return undefined;
}

function getRecord(value: unknown): Record<string, unknown> | undefined {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return undefined;
  return value as Record<string, unknown>;
}

function getList(value: unknown) {
  return Array.isArray(value) ? value : [];
}

function formatValue(value: unknown): string {
  if (value == null) return '-';
  if (typeof value === 'string') return normalizeRisk(value) || flagLabels[value] || value;
  if (typeof value === 'number') {
    return value.toLocaleString('tr-TR', { maximumFractionDigits: 2 });
  }
  if (typeof value === 'boolean') {
    return value ? 'Var' : 'Yok';
  }

  if (Array.isArray(value)) {
    return value.map(formatValue).join(', ');
  }

  if (typeof value === 'object') {
    const record = value as Record<string, unknown>;
    const preferred =
      getString(record.label) ||
      getString(record.name) ||
      getString(record.title) ||
      getString(record.description) ||
      getString(record.action) ||
      getString(record.reason);

    return preferred || JSON.stringify(value);
  }

  return String(value);
}

function humanize(value: string) {
  const label = metricLabels[value] || flagLabels[value];
  if (label) return label;
  return value
    .replace(/_/g, ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}
