const DEFAULT_AI_CFO_BACKEND_URL = 'http://localhost:8000';

export function getAiCfoBackendBaseUrl() {
  const configuredUrl = process.env.CFO_BACKEND_CHAT_URL?.trim();

  if (!configuredUrl) {
    return DEFAULT_AI_CFO_BACKEND_URL;
  }

  return configuredUrl.replace(/\/ask$/, '').replace(/\/$/, '');
}
