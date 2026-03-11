/** F3: Shared email validation - RFC 5322 simplified (local@domain.tld) */
const EMAIL_REGEX = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export function isValidEmail(email: string): boolean {
  return !!email?.trim() && EMAIL_REGEX.test(email.trim());
}

/**
 * Simple email typosquatting detection for common domains.
 */
const COMMON_DOMAINS = [
  "gmail.com",
  "yahoo.com",
  "hotmail.com",
  "outlook.com",
  "icloud.com",
  "aol.com",
  "msn.com",
];

const TYPO_MAP: Record<string, string[]> = {
  "gmail.com": [
    "gnail.com",
    "gmali.com",
    "gmal.com",
    "gmai.com",
    "gail.com",
    "googlemail.com",
    "gmail.co",
    "gmial.com",
    "gmeil.com",
  ],
  "gmail.co.uk": ["gmial.co.uk", "gmail.couk"],
  "yahoo.com": ["yaho.com", "yahho.com", "yhaoo.com", "yahooo.com", "yahoo.co"],
  "yahoo.co.uk": ["yaho.co.uk", "yahoo.couk"],
  "yahoo.ca": ["yaho.ca"],
  "yahoo.com.au": ["yaho.com.au"],
  "hotmail.com": ["hotmial.com", "hotmal.com", "hotmale.com", "hotmai.com"],
  "hotmail.co.uk": ["hotmial.co.uk", "hotmail.couk"],
  "outlook.com": [
    "outlok.com",
    "outllok.com",
    "outloock.com",
    "outlookk.com",
    "outloo.com",
  ],
  "outlook.co.uk": ["outlook.couk"],
  "icloud.com": ["icould.com", "iclod.com", "icloud.co", "icload.com"],
  "aol.com": ["ao.com", "aoll.com", "aol.co"],
  "msn.com": ["msn.co", "mns.com"],
  "gmx.de": ["gmx.d", "gmx.com"],
  "gmx.com": ["gmx.co"],
  "protonmail.com": ["protonmail.co", "proton.me"],
  "qq.com": ["qq.cn", "qq.con"],
  "live.com": ["live.co", "live.co.uk"],
  "ymail.com": ["ymail.co"],
  "mail.com": ["mail.co"],
  "zoho.com": ["zoho.co"],
};

export function checkEmailTypo(email: string): string | null {
  if (!email?.includes("@")) return null;

  const domain = email.split("@")[1].toLowerCase();

  // Direct match in typo map
  for (const [correct, typos] of Object.entries(TYPO_MAP)) {
    if (typos.includes(domain)) {
      return correct;
    }
  }

  // Basic Levenshtein-like check for small distance could go here if needed,
  // but for high-impact fixes, a curated list is often safer.

  return null;
}
