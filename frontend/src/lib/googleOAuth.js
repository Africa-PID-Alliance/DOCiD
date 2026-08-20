const PRIVATE_IPV4 =
  /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/;

/**
 * Google rejects RFC1918 private IPs as OAuth redirect URIs.
 * nip.io keeps the same LAN host while presenting a hostname Google accepts.
 * @see https://stackoverflow.com/questions/24736168/error-invalid-request-device-id-and-device-name-are-required-for-private-ip
 */
export function getGoogleRedirectUri() {
  const configured = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI;
  if (!configured) {
    return configured;
  }

  try {
    const redirectUrl = new URL(configured);
    if (PRIVATE_IPV4.test(redirectUrl.hostname)) {
      redirectUrl.hostname = `${redirectUrl.hostname}.nip.io`;
    }
    return redirectUrl.toString().replace(/\/$/, '');
  } catch {
    return configured;
  }
}
