import Image from 'next/image';
import Link from 'next/link';

const metrics = [
  { label: 'Nakit dayanma süresi', value: '42 gün', tone: 'text-emerald-600' },
  { label: 'Risk skoru', value: '68 / 100', tone: 'text-amber-600' },
  { label: 'Açık aksiyon', value: '7', tone: 'text-sky-600' },
];

const agents = [
  'Nakit Akışı Agentı',
  'Risk Önceliklendirme',
  'Pazarlama Agentı',
  'CFO Yanıt Üretici',
];

const workflows = [
  {
    title: 'Finans sorularını sor',
    body: 'Nakit, pazarlama, gider, makro veri ve risk sinyallerini tek CFO çalışma alanından sorgula.',
  },
  {
    title: 'Agent destekli analiz al',
    body: 'Her soru doğru agentlara yönlendirilir ve net bir yönetici özetiyle geri döner.',
  },
  {
    title: 'Risk sinyallerine göre aksiyon al',
    body: 'Nakit baskısı kritikleşmeden önce öncelikli aksiyonları, uyarıları ve önerileri gör.',
  },
];

export default async function Home() {
  return (
    <main className="bg-white text-gray-800 dark:bg-dark-primary dark:text-white/90">
      <section className="border-b border-gray-100 py-16 dark:border-gray-800 lg:py-20">
        <div className="wrapper grid items-center gap-12 lg:grid-cols-[1fr_520px]">
          <div>
            <p className="mb-4 text-sm font-semibold uppercase tracking-wide text-primary-500">
              AI CFO Platformu
            </p>
            <h1 className="max-w-[720px] text-4xl font-bold leading-tight text-gray-900 dark:text-white sm:text-5xl">
              Nakit akışı, risk ve yönetici kararları için finans zekası.
            </h1>
            <p className="mt-5 max-w-[620px] text-base leading-7 text-gray-500 dark:text-gray-400">
              Şirket çalışma alanına bağlan, finans sorularını doğal dille sor
              ve uzman agentların CFO seviyesinde analiz hazırlamasını sağla.
            </p>

            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <Link
                href="/signin?next=/dashboard"
                className="inline-flex h-12 items-center justify-center rounded-full bg-primary-500 px-6 text-sm font-semibold text-white transition hover:bg-primary-600"
              >
                CFO çalışma alanını aç
              </Link>
              <Link
                href="/dashboard"
                className="inline-flex h-12 items-center justify-center rounded-full border border-gray-200 px-6 text-sm font-semibold text-gray-700 transition hover:border-gray-300 hover:bg-gray-50 dark:border-gray-700 dark:text-gray-300 dark:hover:bg-white/5"
              >
                Dashboarda git
              </Link>
            </div>
          </div>

          <div className="rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-white/10 dark:bg-white/[0.03]">
            <div className="rounded-md bg-white p-5 shadow-theme-xs dark:bg-dark-secondary">
              <div className="flex items-start justify-between gap-4 border-b border-gray-100 pb-4 dark:border-white/10">
                <div>
                  <p className="text-sm text-gray-500 dark:text-gray-400">
                    Yönetici özeti
                  </p>
                  <h2 className="mt-1 text-xl font-bold text-gray-900 dark:text-white">
                    Mayıs nakit baskısı artıyor
                  </h2>
                </div>
                <span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-500/10 dark:text-amber-300">
                  İncele
                </span>
              </div>

              <div className="mt-5 grid gap-3 sm:grid-cols-3">
                {metrics.map((metric) => (
                  <div
                    key={metric.label}
                    className="rounded-md border border-gray-100 bg-white p-3 dark:border-white/10 dark:bg-white/[0.03]"
                  >
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {metric.label}
                    </p>
                    <p className={`mt-1 text-lg font-bold ${metric.tone}`}>
                      {metric.value}
                    </p>
                  </div>
                ))}
              </div>

              <div className="mt-5 space-y-3">
                {agents.map((agent) => (
                  <div
                    key={agent}
                    className="flex items-center justify-between rounded-md border border-gray-100 px-3 py-2 text-sm dark:border-white/10"
                  >
                    <span>{agent}</span>
                    <span className="text-xs font-medium text-emerald-600">
                      Hazır
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="py-14">
        <div className="wrapper">
          <div className="max-w-[720px]">
            <p className="text-sm font-semibold uppercase tracking-wide text-primary-500">
              Çalışma alanı neleri yönetir?
            </p>
            <h2 className="mt-3 text-3xl font-bold text-gray-900 dark:text-white">
              Finans soruları ve agent iş akışları için tek arayüz.
            </h2>
          </div>

          <div className="mt-8 grid gap-4 md:grid-cols-3">
            {workflows.map((workflow) => (
              <article
                key={workflow.title}
                className="rounded-lg border border-gray-200 p-5 dark:border-white/10"
              >
                <h3 className="text-base font-bold text-gray-900 dark:text-white">
                  {workflow.title}
                </h3>
                <p className="mt-3 text-sm leading-6 text-gray-500 dark:text-gray-400">
                  {workflow.body}
                </p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="border-t border-gray-100 py-14 dark:border-gray-800">
        <div className="wrapper grid items-center gap-10 lg:grid-cols-[420px_1fr]">
          <Image
            src="/images/dashboard/Saly.png"
            alt="AI CFO panel önizlemesi"
            width={420}
            height={320}
            className="mx-auto max-h-[320px] w-auto object-contain"
          />
          <div>
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white">
              Bu projedeki backend agentları etrafında tasarlandı.
            </h2>
            <p className="mt-4 max-w-[680px] text-base leading-7 text-gray-500 dark:text-gray-400">
              Frontend artık API ile aynı ürün dilini konuşuyor: kimlik
              doğrulamalı şirket çalışma alanları, AI CFO sohbeti, agent
              seçimi, nakit akışı özetleri, risk sinyalleri ve yönetici
              önerileri.
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
