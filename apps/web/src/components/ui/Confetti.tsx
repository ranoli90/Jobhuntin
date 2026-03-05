import * as React from "react";

const PARTICLE_COUNT = 24;
const COLORS = [
    "#6366f1", // primary
    "#a855f7", // purple
    "#ec4899", // pink
    "#f59e0b", // amber
    "#10b981", // emerald
    "#3b82f6", // blue
];

interface Particle {
    id: number;
    x: number;
    color: string;
    size: number;
    angle: number;
    delay: number;
    duration: number;
    shape: "circle" | "square" | "star";
}

function generateParticles(): Particle[] {
    return Array.from({ length: PARTICLE_COUNT }, (_, i) => ({
        id: i,
        x: 40 + Math.random() * 20, // cluster around center (40–60%)
        color: COLORS[Math.floor(Math.random() * COLORS.length)],
        size: 4 + Math.random() * 8,
        angle: Math.random() * 360,
        delay: Math.random() * 0.3,
        duration: 1 + Math.random() * 1.2,
        shape: (["circle", "square", "star"] as const)[
            Math.floor(Math.random() * 3)
        ],
    }));
}

interface ConfettiProps {
    /** Set to true to trigger the burst */
    active: boolean;
    /** Called when animation completes */
    onComplete?: () => void;
    className?: string;
}

export function Confetti({ active, onComplete, className = "" }: ConfettiProps) {
    const [particles, setParticles] = React.useState<Particle[]>([]);
    const prefersReducedMotion =
        typeof window !== "undefined" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    React.useEffect(() => {
        if (!active || prefersReducedMotion) return;

        setParticles(generateParticles());

        const timer = setTimeout(() => {
            setParticles([]);
            onComplete?.();
        }, 2500);

        return () => clearTimeout(timer);
    }, [active, prefersReducedMotion, onComplete]);

    if (!active || particles.length === 0 || prefersReducedMotion) return null;

    return (
        <div
            className={`pointer-events-none fixed inset-0 z-[100] overflow-hidden ${className}`}
            aria-hidden="true"
        >
            {particles.map((p) => (
                <div
                    key={p.id}
                    className="absolute animate-confetti-fall"
                    style={{
                        left: `${p.x}%`,
                        top: "-5%",
                        width: p.size,
                        height: p.size,
                        backgroundColor: p.shape !== "star" ? p.color : "transparent",
                        borderRadius: p.shape === "circle" ? "50%" : p.shape === "square" ? "2px" : undefined,
                        borderLeft: p.shape === "star" ? `${p.size / 2}px solid transparent` : undefined,
                        borderRight: p.shape === "star" ? `${p.size / 2}px solid transparent` : undefined,
                        borderBottom: p.shape === "star" ? `${p.size}px solid ${p.color}` : undefined,
                        animationDelay: `${p.delay}s`,
                        animationDuration: `${p.duration}s`,
                        transform: `rotate(${p.angle}deg)`,
                    }}
                />
            ))}
        </div>
    );
}
