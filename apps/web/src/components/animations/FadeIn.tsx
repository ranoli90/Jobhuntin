import React, { useState, useEffect, useRef } from 'react';
import { cn } from '../../lib/utils';

interface FadeInProps {
    children: React.ReactNode;
    className?: string;
    delay?: number;
    threshold?: number;
}

export function FadeIn({
    children,
    className = "",
    delay = 0,
    threshold = 0.08
}: FadeInProps) {
    const ref = useRef<HTMLDivElement>(null);
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        const el = ref.current;
        if (!el) return;

        const observer = new IntersectionObserver(([entry]) => {
            if (entry.isIntersecting) {
                setVisible(true);
                observer.disconnect();
            }
        }, { threshold });

        observer.observe(el);
        return () => observer.disconnect();
    }, [threshold]);

    return (
        <div
            ref={ref}
            className={cn(
                "transition-all duration-700 ease-out",
                visible ? "opacity-100 translate-y-0" : "opacity-0 translate-y-10",
                className
            )}
            style={{ transitionDelay: `${delay}ms` }}
        >
            {children}
        </div>
    );
}
