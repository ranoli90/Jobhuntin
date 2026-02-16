import React from 'react';
import { Bot } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';

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
            <div className={cn(
                "bg-gradient-to-br from-blue-500 via-violet-500 to-pink-500 shadow-lg shadow-violet-500/30 transition-all duration-300 group-hover:shadow-violet-500/50 group-hover:scale-105",
                currentSize.iconBox
            )}>
                <Bot className={cn("text-white", currentSize.bot)} />
            </div>
            {!iconOnly && (
                <span className={cn(
                    "font-black font-display tracking-tight transition-colors",
                    variant === 'dark' 
                        ? "text-white group-hover:text-blue-400" 
                        : "text-slate-900 group-hover:text-blue-600",
                    currentSize.text
                )}>
                    JobHuntin.com
                </span>
            )}
        </div>
    );

    if (to) {
        return (
            <Link to={to} onClick={onClick} className="inline-block">
                {content}
            </Link>
        );
    }

    return content;
}
