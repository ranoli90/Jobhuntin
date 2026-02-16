/**
 * Formats a phone number with flexible international support.
 * US numbers: (XXX) XXX-XXXX
 * International: +XX XXX XXX XXXX (preserves country code)
 */
export function formatPhoneNumber(value: string): string {
    if (!value) return value;

    const digits = value.replace(/[^\d+]/g, "");
    
    if (digits.startsWith("+")) {
        const numberPart = digits.slice(1);
        if (numberPart.length <= 2) return `+${numberPart}`;
        if (numberPart.length <= 5) return `+${numberPart.slice(0, 2)} ${numberPart.slice(2)}`;
        if (numberPart.length <= 8) return `+${numberPart.slice(0, 2)} ${numberPart.slice(2, 5)} ${numberPart.slice(5)}`;
        return `+${numberPart.slice(0, 2)} ${numberPart.slice(2, 5)} ${numberPart.slice(5, 8)} ${numberPart.slice(8, 12)}`;
    }

    if (digits.length === 11 && digits.startsWith("1")) {
        const num = digits.slice(1);
        return `+1 (${num.slice(0, 3)}) ${num.slice(3, 6)}-${num.slice(6, 10)}`;
    }

    if (digits.length < 4) return digits;
    if (digits.length < 7) {
        return `(${digits.slice(0, 3)}) ${digits.slice(3)}`;
    }

    return `(${digits.slice(0, 3)}) ${digits.slice(3, 6)}-${digits.slice(6, 10)}`;
}

/**
 * Validates a phone number - basic validation for common formats
 * Returns true if the phone number appears valid, false otherwise
 */
export function isValidPhoneNumber(value: string): boolean {
    if (!value) return true; // Phone is optional
    
    // Remove all non-digit characters except +
    const cleaned = value.replace(/[^\d+]/g, "");
    
    // Check for valid length (10-15 digits, optionally with + prefix)
    if (cleaned.startsWith("+")) {
        const numberPart = cleaned.slice(1);
        return /^\d{10,15}$/.test(numberPart);
    }
    
    // US number: 10 digits, or 11 digits starting with 1
    if (/^\d{10}$/.test(cleaned)) return true;
    if (/^1\d{10}$/.test(cleaned)) return true;
    
    // International: 10-15 digits
    return /^\d{10,15}$/.test(cleaned);
}
