import React, { createContext, useContext, useEffect, useState, useRef, useCallback } from "react";
import type { Session, User } from "@supabase/supabase-js";
import { supabase } from "../lib/supabase";
import { useNavigate } from "react-router-dom";

export interface AuthState {
    session: Session | null;
    user: User | null;
    loading: boolean;
    signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthState | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [session, setSession] = useState<Session | null>(null);
    const [loading, setLoading] = useState(true);
    const loadingRef = useRef(true);

    // Create a navigate function that is safe to use outside of Router context if needed,
    // but AuthProvider is inside BrowserRouter in main.tsx, so this is fine.
    const navigate = useNavigate();

    const signOut = useCallback(async () => {
        await supabase.auth.signOut();
        setSession(null);
        navigate("/login");
    }, [navigate]);

    useEffect(() => {
        let mounted = true;
        loadingRef.current = loading;

        const initializeAuth = async () => {
            try {
                const hash = window.location.hash;
                if (hash && (hash.includes('access_token') || hash.includes('type=magiclink'))) {
                    console.log("Detected magic link hash, waiting for session...");
                    // Still call getSession() — Supabase will process the hash fragment
                    // and exchange it for a session. Without this, loading stays true
                    // until onAuthStateChange fires or the 4s timeout hits.
                    const { data } = await supabase.auth.getSession();
                    if (mounted) {
                        setSession(data.session ?? null);
                        setLoading(false);
                    }
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
            console.log("Auth state changed:", event);
            if (mounted) {
                setSession(nextSession);
                setLoading(false);

                // Save a minimal auth signal for extension sync.
                // SECURITY: Do NOT store tokens in localStorage — only a
                // lightweight flag so the extension content script knows the
                // user is logged in. The actual session is managed by the
                // Supabase SDK via its own storage key.
                if (nextSession) {
                    localStorage.setItem('sorce-session', JSON.stringify({
                        logged_in: true,
                        ts: Date.now(),
                    }));
                } else {
                    localStorage.removeItem('sorce-session');
                }
            }
        });

        const timeout = setTimeout(() => {
            if (mounted && loadingRef.current) {
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
    }, []); // Logic moved from useAuth

    useEffect(() => {
        loadingRef.current = loading;
    }, [loading]);

    const value = {
        session,
        user: session?.user ?? null,
        loading,
        signOut,
    };

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    );
}

export function useAuthContext() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error("useAuthContext must be used within an AuthProvider");
    }
    return context;
}
