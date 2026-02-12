// Supabase client is no longer used. This file returns a proxy
// to avoid breaking legacy imports while providing a clear error on use.

export const supabase = new Proxy(
  {},
  {
    get: (_target, prop) => {
      // Allow internal properties to avoid crashes
      if (typeof prop === 'string' && prop === 'then') return undefined;

      return (...args: any[]) => {
        console.error(
          `Attempted to call Supabase.${String(prop)} but Supabase is removed.`
        );
        return Promise.reject(new Error("Supabase is removed"));
      };
    },
  }
) as any;
