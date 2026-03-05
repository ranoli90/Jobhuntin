import React from 'react';
import { Bot, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';
import { cn } from '../../lib/utils';
import { motion, AnimatePresence } from 'framer-motion';

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
                whileHover={{ scale: 1.1, rotate: [0, -10, 10, 0] }}
                transition={{ duration: 0.6, ease: "easeInOut" }}
                className={cn(
                    variant === 'dark'
                        ? "bg-white/10 backdrop-blur-sm shadow-sm transition-all duration-300 group-hover:bg-white/20"
                        : "bg-gradient-to-br from-brand-sunrise via-brand-plum to-brand-lagoon shadow-xl shadow-brand-sunrise/30 transition-all duration-300 group-hover:shadow-brand-sunrise/40 group-hover:shadow-2xl",
                    currentSize.iconBox,
                    "relative overflow-hidden"
                )}
            >
                {/* Animated gradient overlay */}
                <motion.div
                    className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/30 to-transparent"
                    initial={{ x: '-100%' }}
                    whileHover={{ x: '100%' }}
                    transition={{ duration: 0.8, ease: "easeInOut" }}
                />
                
                {/* Sparkle particles */}
                <AnimatePresence>
                    {size === 'lg' && (
                        <>
                            {[...Array(3)].map((_, i) => (
                                <motion.div
                                    key={i}
                                    className="absolute w-1 h-1 bg-white rounded-full"
                                    initial={{ 
                                        opacity: 0, 
                                        scale: 0,
                                        x: 0,
                                        y: 0
                                    }}
                                    animate={{ 
                                        opacity: [0, 1, 0],
                                        scale: [0, 1, 0],
                                        x: [0, Math.random() * 20 - 10],
                                        y: [0, -20 - Math.random() * 10]
                                    }}
                                    transition={{ 
                                        duration: 2 + i * 0.3, 
                                        repeat: Infinity, 
                                        repeatDelay: 1 + i * 0.5,
                                        ease: "easeOut"
                                    }}
                                    style={{
                                        left: `${20 + i * 15}%`,
                                        top: `${30 + i * 10}%`
                                    }}
                                />
                            ))}
                        </>
                    )}
                </AnimatePresence>

                <Bot className={cn("text-white drop-shadow-sm relative z-10", currentSize.bot)} aria-hidden />
            </motion.div>
            {!iconOnly && (
                <motion.span 
                    className={cn(
                        "font-black tracking-[-0.04em] transition-all duration-300",
                        variant === 'dark'
                            ? "text-white group-hover:text-brand-sunrise"
                            : "text-transparent bg-clip-text bg-gradient-to-r from-brand-plum via-brand-sunrise to-brand-lagoon group-hover:from-brand-sunrise group-hover:via-brand-lagoon group-hover:to-brand-plum group-hover:tracking-[-0.03em]",
                        currentSize.text
                    )}
                    whileHover={{ scale: 1.05 }}
                    transition={{ duration: 0.3 }}
                >
                    JobHuntin
                </motion.span>
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
