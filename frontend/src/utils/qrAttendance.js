const USER_QR_PATTERN = /^USER:(\d+)$/;

export function parseUserQr(decodedText) {
  const match = String(decodedText || '').trim().match(USER_QR_PATTERN);
  if (!match) return null;

  return Number(match[1]);
}
