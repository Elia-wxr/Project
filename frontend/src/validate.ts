export type BaseUrlResult =
  | { ok: true; normalized: string }
  | { ok: false; message: string };

const COMPLETIONS = /\/chat\/completions\/?$/i;

export function normalizeBaseUrl(value: string): string {
  const trimmed = value.trim();
  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    return trimmed;
  }
  let path = url.pathname;
  if (path === '/') {
    path = '';
  } else if (path.endsWith('/')) {
    path = path.slice(0, -1);
  }
  return `${url.protocol}//${url.host}${path}`;
}

function isLoopback(hostname: string): boolean {
  const host = hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (host === 'localhost' || host === '::1') {
    return true;
  }
  const ip = ipv4(host);
  return ip !== null && ip[0] === 127;
}

function ipv4(host: string): [number, number, number, number] | null {
  const match = /^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$/.exec(host);
  if (!match) {
    return null;
  }
  const parts = match.slice(1).map(part => Number(part));
  if (parts.some(part => part > 255)) {
    return null;
  }
  return parts as [number, number, number, number];
}

function isBlockedHost(hostname: string): boolean {
  const host = hostname.toLowerCase().replace(/^\[|\]$/g, '');
  if (host === 'metadata.google.internal' || host.endsWith('.metadata.google.internal')) {
    return true;
  }
  if (isLoopback(host)) {
    return false;
  }
  const ip = ipv4(host);
  if (!ip) {
    return false;
  }
  const [a, b] = ip;
  // 0.0.0.0/8 and link-local are never a model gateway.
  // Private and carrier-grade ranges are decided by the server admin allowlist.
  if (a === 0 || (a === 169 && b === 254)) {
    return true;
  }
  return false;
}

export function validateBaseUrl(value: string): BaseUrlResult {
  const trimmed = value.trim();
  if (!trimmed) {
    return { ok: false, message: 'Enter a Base URL.' };
  }
  let url: URL;
  try {
    url = new URL(trimmed);
  } catch {
    return { ok: false, message: 'Enter a valid Base URL, such as https://api.openai.com/v1.' };
  }
  if (url.username || url.password) {
    return { ok: false, message: 'Remove the username and password from the Base URL.' };
  }
  if (url.search) {
    return { ok: false, message: 'Remove the query string. Use only the API base URL.' };
  }
  if (url.hash) {
    return { ok: false, message: 'Remove the fragment. Use only the API base URL.' };
  }
  if (COMPLETIONS.test(url.pathname)) {
    return { ok: false, message: "Use the server's API base URL, not /chat/completions." };
  }
  if (url.protocol !== 'https:' && url.protocol !== 'http:') {
    return { ok: false, message: 'Use an http or https Base URL.' };
  }
  if (url.protocol === 'http:' && !isLoopback(url.hostname)) {
    return {
      ok: false,
      message: 'Local HTTP is only allowed for a loopback address. Use HTTPS for other servers.'
    };
  }
  if (isBlockedHost(url.hostname)) {
    return { ok: false, message: 'This address is not allowed. Use a public HTTPS server or loopback.' };
  }
  return { ok: true, normalized: normalizeBaseUrl(trimmed) };
}

/** Whole seconds from 5 to 120. Rejects NaN, exponents, decimals and padded strings. */
export function parseTimeout(text: string): number | null {
  const trimmed = text.trim();
  if (!/^(?:[5-9]|[1-9]\d|1[01]\d|120)$/.test(trimmed)) {
    return null;
  }
  const value = Number(trimmed);
  if (!Number.isInteger(value) || value < 5 || value > 120) {
    return null;
  }
  return value;
}
