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
    "gmail.com": ["gnail.com", "gmali.com", "gmal.com", "gmai.com", "gail.com", "googlemail.com"],
    "yahoo.com": ["yaho.com", "yahho.com", "yhaoo.com"],
    "hotmail.com": ["hotmial.com", "hotmal.com", "hotmale.com"],
};

export function checkEmailTypo(email: string): string | null {
    if (!email || !email.includes("@")) return null;

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
