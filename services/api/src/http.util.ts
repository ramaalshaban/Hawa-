import { HTTP_TIMEOUT_MS } from './config';

/**
 * JSON request with a hard timeout. Throws on network errors, timeouts and non-2xx
 * responses, so the Kafka handler fails and the message is retried (no silent catch).
 */
export async function fetchJson<T>(
  url: string,
  init: { method?: string; body?: unknown } = {},
): Promise<T> {
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), HTTP_TIMEOUT_MS);
  try {
    const res = await fetch(url, {
      method: init.method ?? 'GET',
      headers: init.body ? { 'content-type': 'application/json' } : undefined,
      body: init.body ? JSON.stringify(init.body) : undefined,
      signal: ctrl.signal,
    });
    if (!res.ok) {
      throw new Error(`${url} -> HTTP ${res.status}: ${(await res.text()).slice(0, 200)}`);
    }
    return (await res.json()) as T;
  } finally {
    clearTimeout(timer);
  }
}
