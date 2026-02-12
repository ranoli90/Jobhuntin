import { useState, useEffect, createContext, useContext, useCallback, ReactNode } from "react";

interface FeatureFlags {
  [key: string]: boolean;
}

interface FeatureFlagContextValue {
  flags: FeatureFlags;
  isEnabled: (flag: string) => boolean;
  setFlag: (flag: string, value: boolean) => void;
  loading: boolean;
}

const FeatureFlagContext = createContext<FeatureFlagContextValue | null>(null);

const LOCAL_STORAGE_KEY = "feature_flags";

const DEFAULT_FLAGS: FeatureFlags = {
  semantic_matching: true,
  ats_scoring: true,
  resume_tailoring: true,
  cover_letter_gen: true,
  batch_matching: true,
  advanced_analytics: false,
  experimental_ui: false,
};

function loadLocalFlags(): FeatureFlags {
  if (typeof window === "undefined") return DEFAULT_FLAGS;
  try {
    const stored = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (stored) {
      return { ...DEFAULT_FLAGS, ...JSON.parse(stored) };
    }
  } catch {
    console.warn("Failed to load feature flags from localStorage");
  }
  return DEFAULT_FLAGS;
}

function saveLocalFlags(flags: FeatureFlags): void {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(flags));
  } catch {
    console.warn("Failed to save feature flags to localStorage");
  }
}

export interface FeatureFlagProviderProps {
  children: ReactNode;
  supabaseClient?: {
    from: (table: string) => {
      select: (columns: string) => {
        eq: (column: string, value: string) => {
          single: () => Promise<{ data: FeatureFlags | null; error: Error | null }>;
        };
      };
    };
  };
  tenantId?: string;
  initialFlags?: FeatureFlags;
}

export function FeatureFlagProvider({
  children,
  supabaseClient,
  tenantId,
  initialFlags,
}: FeatureFlagProviderProps) {
  const [flags, setFlags] = useState<FeatureFlags>(initialFlags ?? loadLocalFlags);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchFlags() {
      if (!supabaseClient || !tenantId) {
        setLoading(false);
        return;
      }

      try {
        const { data, error } = await supabaseClient
          .from("feature_flags")
          .select("flags")
          .eq("tenant_id", tenantId)
          .single();

        if (data && !error) {
          setFlags(prev => ({ ...prev, ...data }));
        }
      } catch (err) {
        console.warn("Failed to fetch feature flags from Supabase:", err);
      }

      setLoading(false);
    }

    fetchFlags();
  }, [supabaseClient, tenantId]);

  const isEnabled = useCallback(
    (flag: string): boolean => {
      return flags[flag] ?? false;
    },
    [flags]
  );

  const setFlag = useCallback((flag: string, value: boolean) => {
    setFlags(prev => {
      const updated = { ...prev, [flag]: value };
      saveLocalFlags(updated);
      return updated;
    });
  }, []);

  return (
    <FeatureFlagContext.Provider value={{ flags, isEnabled, setFlag, loading }}>
      {children}
    </FeatureFlagContext.Provider>
  );
}

export function useFeatureFlags() {
  const context = useContext(FeatureFlagContext);
  if (!context) {
    throw new Error("useFeatureFlags must be used within a FeatureFlagProvider");
  }
  return context;
}

export function useFeatureFlag(flagName: string): boolean {
  const { isEnabled, loading } = useFeatureFlags();

  if (loading) {
    return DEFAULT_FLAGS[flagName] ?? false;
  }

  return isEnabled(flagName);
}

export function useSetFeatureFlag() {
  const { setFlag } = useFeatureFlags();
  return setFlag;
}

export { DEFAULT_FLAGS };
