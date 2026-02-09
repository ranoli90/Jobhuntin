import { useState } from "react";
import { apiPost } from "../lib/api";

export interface CoverLetterResponse {
    content: string;
    subject_line: string;
}

export function useCoverLetter() {
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [result, setResult] = useState<CoverLetterResponse | null>(null);

    const generate = async (profile: any, job: any, tone: string = "professional") => {
        setLoading(true);
        setError(null);
        try {
            const data = await apiPost<CoverLetterResponse>("/ai/generate-cover-letter", {
                profile,
                job,
                tone,
            });
            setResult(data);
            return data;
        } catch (err: any) {
            console.error(err);
            setError(err.message || "Failed to generate cover letter");
            throw err;
        } finally {
            setLoading(false);
        }
    };

    return { generate, loading, error, result };
}
