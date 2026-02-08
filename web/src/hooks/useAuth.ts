import { useEffect, useState, useCallback } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { useNavigate } from "react-router-dom";

export interface AuthState {
  session: Session | null;
  user: User | null;
  loading: boolean;
  signOut: () => Promise<void>;
}

export function useAuth(): AuthState {
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  const signOut = useCallback(async () => {
    await supabase.auth.signOut();
  }, []);

  useEffect(() => {
    let mounted = true;

    const initializeAuth = async () => {
      try {
        // Handle the hash fragment from magic link redirect manually if Supabase client doesn't pick it up automatically
        const hash = window.location.hash;
        if (hash && (hash.includes('access_token') || hash.includes('type=magiclink'))) {
            // Wait briefly for Supabase to process the hash automatically
            // This is safer than manually calling getSession() immediately which might race
            console.log("Detected magic link hash, waiting for session...");
            // We don't set loading to false yet, we wait for onAuthStateChange or a timeout
        } else {
             const { data } = await supabase.auth.getSession();
             if (mounted) {
               setSession(data.session ?? null);
               setLoading(false);
             }
        }
      } catch (error) {
        console.error("Failed to get session:", error);
        if (mounted) setLoading(false);
      }
    };

    initializeAuth();

    const { data: subscription } = supabase.auth.onAuthStateChange((event, nextSession) => {
      console.log("Auth state changed:", event, nextSession?.user?.email);
      if (mounted) {
        setSession(nextSession);
        setLoading(false);
      }
    });

    // Fallback: If we are stuck in loading state (e.g. hash was present but Supabase failed to process it)
    const timeout = setTimeout(() => {
        if (mounted && loading) {
            console.log("Auth loading timeout reached, forcing completion");
            supabase.auth.getSession().then(({ data }) => {
                if (mounted) {
                    setSession(data.session);
                    setLoading(false);
                }
            });
        }
    }, 4000);

    return () => {
      mounted = false;
      clearTimeout(timeout);
      subscription?.subscription?.unsubscribe();
    };
  }, []); // Remove 'loading' from dependency array to avoid re-running

  return {
    session,
    user: session?.user ?? null,
    loading,
    signOut,
  };
}
