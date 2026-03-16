import fs from 'fs';
import path from 'path';
import { createHash } from 'crypto';
import { fileURLToPath } from 'url';

import { seoLogger } from './logger';
import { incrementCounter, SEO_METRIC_NAMES } from './metrics';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const STATE_FILE = path.resolve(__dirname, '../../logs/seo-deduplication-state.json');
const DEFAULT_SUBMISSION_WINDOW_HOURS = 24 * 7;

interface DeduplicationRecord {
    firstSeenAt: string;
    lastSeenAt: string;
    metadata?: Record<string, unknown>;
}

interface SubmissionRecord {
    firstSubmittedAt: string;
    lastSubmittedAt: string;
    status: 'success' | 'error';
    metadata?: Record<string, unknown>;
}

interface DeduplicationState {
    contentKeys: Record<string, DeduplicationRecord>;
    contentFingerprints: Record<string, DeduplicationRecord>;
    urlSubmissions: Record<string, SubmissionRecord>;
}

function getEmptyState(): DeduplicationState {
    return {
        contentKeys: {},
        contentFingerprints: {},
        urlSubmissions: {},
    };
}

function ensureStateDirectory(): void {
    const directory = path.dirname(STATE_FILE);
    if (!fs.existsSync(directory)) {
        fs.mkdirSync(directory, { recursive: true });
    }
}

function loadState(): DeduplicationState {
    try {
        if (!fs.existsSync(STATE_FILE)) {
            return getEmptyState();
        }

        const parsed = JSON.parse(fs.readFileSync(STATE_FILE, 'utf-8')) as Partial<DeduplicationState>;
        return {
            contentKeys: parsed.contentKeys || {},
            contentFingerprints: parsed.contentFingerprints || {},
            urlSubmissions: parsed.urlSubmissions || {},
        };
    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        seoLogger.warn('Failed to load SEO deduplication state. Continuing with empty state.', {
            stateFile: STATE_FILE,
            error: errorMessage,
        });
        return getEmptyState();
    }
}

function saveState(state: DeduplicationState): void {
    try {
        ensureStateDirectory();
        fs.writeFileSync(STATE_FILE, JSON.stringify(state, null, 2));
    } catch (error: unknown) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        seoLogger.warn('Failed to persist SEO deduplication state.', {
            stateFile: STATE_FILE,
            error: errorMessage,
        });
    }
}

function recordDuplicate(type: string, key: string, metadata?: Record<string, unknown>): void {
    incrementCounter(SEO_METRIC_NAMES.CONTENT_DUPLICATES, 1, { type });
    seoLogger.warn('Duplicate SEO work suppressed', {
        type,
        key,
        ...metadata,
    });
}

export function normalizeText(value: string | undefined | null): string {
    if (!value) {
        return '';
    }

    return value
        .normalize('NFKD')
        .replace(/[\u0300-\u036f]/g, '')
        .toLowerCase()
        .trim()
        .replace(/\s+/g, ' ');
}

export function normalizeSlug(value: string | undefined | null): string {
    return normalizeText(value)
        .replace(/[^a-z0-9]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

export function normalizeDomain(value: string | undefined | null): string {
    if (!value) {
        return '';
    }

    try {
        const raw = /^https?:\/\//i.test(value) ? value : `https://${value}`;
        const parsed = new URL(raw);
        const pathname = parsed.pathname.replace(/\/+$/g, '') || '';
        return `${parsed.hostname.toLowerCase().replace(/^www\./, '')}${pathname.toLowerCase()}`;
    } catch {
        return normalizeText(value)
            .replace(/^https?:\/\//, '')
            .replace(/^www\./, '')
            .replace(/\/+$/g, '');
    }
}

export function normalizeUrlFingerprint(url: string): string {
    const parsed = new URL(url);
    const pathname = parsed.pathname.replace(/\/+$/g, '') || '/';
    const searchParams = [...parsed.searchParams.entries()].sort(([left], [right]) => left.localeCompare(right));
    const search = searchParams.length
        ? `?${searchParams
            .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
            .join('&')}`
        : '';

    return `${parsed.protocol}//${parsed.hostname.toLowerCase()}${pathname.toLowerCase()}${search}`;
}

export function createContentKey(parts: Array<string | undefined | null>): string {
    return parts
        .map(part => normalizeSlug(part) || normalizeText(part))
        .filter(Boolean)
        .join('::');
}

export function fingerprintContent(content: string): string {
    return createHash('sha256')
        .update(content.replace(/\r\n/g, '\n').trim())
        .digest('hex');
}

function upsertRecord(recordMap: Record<string, DeduplicationRecord>, key: string, metadata?: Record<string, unknown>): void {
    const now = new Date().toISOString();
    const existing = recordMap[key];

    recordMap[key] = {
        firstSeenAt: existing?.firstSeenAt || now,
        lastSeenAt: now,
        metadata: {
            ...(existing?.metadata || {}),
            ...(metadata || {}),
        },
    };
}

export function hasTrackedContentKey(key: string, metadata?: Record<string, unknown>): boolean {
    const state = loadState();
    const isTracked = Boolean(state.contentKeys[key]);

    if (isTracked) {
        recordDuplicate('content-key', key, metadata);
    }

    return isTracked;
}

export function trackContentKey(key: string, metadata?: Record<string, unknown>): void {
    const state = loadState();
    upsertRecord(state.contentKeys, key, metadata);
    saveState(state);
}

export function hasTrackedContentFingerprint(fingerprint: string, metadata?: Record<string, unknown>): boolean {
    const state = loadState();
    const isTracked = Boolean(state.contentFingerprints[fingerprint]);

    if (isTracked) {
        recordDuplicate('content-fingerprint', fingerprint, metadata);
    }

    return isTracked;
}

export function trackContentFingerprint(fingerprint: string, metadata?: Record<string, unknown>): void {
    const state = loadState();
    upsertRecord(state.contentFingerprints, fingerprint, metadata);
    saveState(state);
}

export function dedupeUrls(urls: string[]): {
    uniqueUrls: string[];
    duplicateCount: number;
    duplicateUrls: string[];
} {
    const seen = new Set<string>();
    const uniqueUrls: string[] = [];
    const duplicateUrls: string[] = [];

    for (const url of urls) {
        const fingerprint = normalizeUrlFingerprint(url);
        if (seen.has(fingerprint)) {
            duplicateUrls.push(url);
            continue;
        }

        seen.add(fingerprint);
        uniqueUrls.push(url);
    }

    if (duplicateUrls.length > 0) {
        seoLogger.warn('Suppressed duplicate URLs within the current submission run', {
            duplicateCount: duplicateUrls.length,
            sample: duplicateUrls.slice(0, 5),
        });
    }

    return {
        uniqueUrls,
        duplicateCount: duplicateUrls.length,
        duplicateUrls,
    };
}

export function getSubmissionDeduplicationWindowMs(): number {
    const rawHours = process.env.SEO_SUBMISSION_DEDUPE_WINDOW_HOURS;
    const parsedHours = rawHours ? Number.parseInt(rawHours, 10) : DEFAULT_SUBMISSION_WINDOW_HOURS;
    const safeHours = Number.isFinite(parsedHours) && parsedHours > 0 ? parsedHours : DEFAULT_SUBMISSION_WINDOW_HOURS;
    return safeHours * 60 * 60 * 1000;
}

export function shouldSkipRecentlySubmittedUrl(
    url: string,
    dedupeWindowMs: number,
    metadata?: Record<string, unknown>
): boolean {
    const state = loadState();
    const fingerprint = normalizeUrlFingerprint(url);
    const record = state.urlSubmissions[fingerprint];

    if (!record || record.status !== 'success') {
        return false;
    }

    const submittedAt = new Date(record.lastSubmittedAt).getTime();
    if (!Number.isFinite(submittedAt)) {
        return false;
    }

    if (Date.now() - submittedAt >= dedupeWindowMs) {
        return false;
    }

    seoLogger.info('Skipping recently submitted URL', {
        url,
        lastSubmittedAt: record.lastSubmittedAt,
        dedupeWindowMs,
        ...metadata,
    });

    return true;
}

export function trackUrlSubmission(
    url: string,
    status: 'success' | 'error',
    metadata?: Record<string, unknown>
): void {
    const state = loadState();
    const fingerprint = normalizeUrlFingerprint(url);
    const now = new Date().toISOString();
    const existing = state.urlSubmissions[fingerprint];

    state.urlSubmissions[fingerprint] = {
        firstSubmittedAt: existing?.firstSubmittedAt || now,
        lastSubmittedAt: now,
        status,
        metadata: {
            ...(existing?.metadata || {}),
            ...(metadata || {}),
        },
    };

    saveState(state);
}
