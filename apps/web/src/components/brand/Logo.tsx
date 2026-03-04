import React from 'react';
import { Bot } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { motion } from 'framer-motion';

interface LogoProps {
    className?: string;
    iconOnly?: boolean;
    to?: string;
    onClick?: () => void;
    size?: 'sm' | 'md' | 'lg';
    variant?: 'light' | 'dark';
}

export function Logo({
    className,
    iconOnly = false,
    to = "/",
    onClick,
    size = 'md',
    variant = 'light'
}: LogoProps) {
    const sizeClasses = {
        sm: {
            container: 'gap-1.5',
            iconBox: 'p-1.5 rounded-lg',
            bot: 'w-4 h-4',
            text: 'text-base'
        },
        md: {
            container: 'gap-2',
            iconBox: 'p-2 rounded-xl',
            bot: 'w-5 h-5',
            text: 'text-xl'
        },
        lg: {
            container: 'gap-3',
            iconBox: 'p-2.5 rounded-2xl',
            bot: 'w-6 h-6',
            text: 'text-2xl'
        }
    };

    const currentSize = sizeClasses[size];

    const content = (
        <div className={cn("flex items-center group relative z-10", currentSize.container, className)}>
            <motion.div
                whileHover={{ scale: 1.05, rotate: [0, -5, 5, 0] }}
                transition={{ duration: 0.4 }}
                className={cn(
                    variant === 'dark'
                        ? "bg-white/10 shadow-sm transition-all duration-300 group-hover:bg-white/20"
                        : "bg-gradient-to-br from-indigo-600 to-indigo-700 shadow-xl shadow-indigo-600/20 transition-all duration-300 group-hover:shadow-indigo-600/30",
                    currentSize.iconBox,
                    "relative overflow-hidden"
                )}
            >
                {/* Shine effect */}
                <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />

                <Bot className={cn("text-white drop-shadow-sm relative z-10", currentSize.bot)} aria-hidden />
            </motion.div>
            {!iconOnly && (
                <span className={cn(
                    "font-black tracking-[-0.04em] transition-all duration-300",
                    variant === 'dark'
                        ? "text-white group-hover:text-indigo-400"
                        : "text-slate-900 group-hover:text-indigo-600 group-hover:tracking-[-0.03em]",
                    currentSize.text
                )}>
                    JobHuntin
                </span>
            )}
        </div>
    );

    if (to) {
        return (
            <Link to={to} onClick={onClick} className="inline-block" aria-label={iconOnly ? "JobHuntin home" : undefined}>
                {content}
            </Link>
        );
    }

    return content;
}
