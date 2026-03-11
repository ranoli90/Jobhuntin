import * as React from "react";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";

interface ProgressiveImageProperties {
  src: string;
  alt: string;
  className?: string;
  containerClassName?: string;
  placeholderColor?: string;
  onLoad?: () => void;
  onError?: () => void;
}

export function ProgressiveImage({
  src,
  alt,
  className,
  containerClassName,
  placeholderColor = "#f1f5f9",
  onLoad,
  onError,
}: ProgressiveImageProperties) {
  const [isLoaded, setIsLoaded] = React.useState(false);
  const [error, setError] = React.useState(false);

  React.useEffect(() => {
    const img = new Image();
    img.src = src;
    img.addEventListener("load", () => {
      setIsLoaded(true);
      onLoad?.();
    });
    img.onerror = () => {
      setError(true);
      onError?.();
    };
  }, [src, onLoad, onError]);

  if (error) {
    return (
      <div
        className={cn(
          "bg-slate-100 flex items-center justify-center",
          containerClassName,
        )}
      >
        <span className="text-slate-400 text-sm">Failed to load image</span>
      </div>
    );
  }

  return (
    <div
      className={cn("relative overflow-hidden", containerClassName)}
      style={{ backgroundColor: placeholderColor }}
    >
      {/* Placeholder/Blur effect */}
      <motion.div
        className="absolute inset-0"
        style={{ backgroundColor: placeholderColor }}
        animate={{ opacity: isLoaded ? 0 : 1 }}
        transition={{ duration: 0.3 }}
      />

      {/* Shimmer loading effect */}
      {!isLoaded && (
        <motion.div
          className="absolute inset-0"
          initial={{ x: "-100%" }}
          animate={{ x: "100%" }}
          transition={{
            repeat: Infinity,
            duration: 1.5,
            ease: "linear",
          }}
          style={{
            background:
              "linear-gradient(90deg, transparent, rgba(255,255,255,0.4), transparent)",
          }}
        />
      )}

      {/* Actual image */}
      <motion.img
        src={src}
        alt={alt}
        className={cn("w-full h-full object-cover", className)}
        initial={{ opacity: 0 }}
        animate={{ opacity: isLoaded ? 1 : 0 }}
        transition={{ duration: 0.3 }}
      />
    </div>
  );
}

// Lazy loading image with intersection observer
interface LazyImageProperties extends ProgressiveImageProperties {
  rootMargin?: string;
  threshold?: number;
}

export function LazyImage({
  src,
  alt,
  rootMargin = "50px",
  threshold = 0.1,
  ...properties
}: LazyImageProperties) {
  const [shouldLoad, setShouldLoad] = React.useState(false);
  const containerReference = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setShouldLoad(true);
          observer.disconnect();
        }
      },
      {
        rootMargin,
        threshold,
      },
    );

    if (containerReference.current) {
      observer.observe(containerReference.current);
    }

    return () => observer.disconnect();
  }, [rootMargin, threshold]);

  return (
    <div ref={containerReference} className={properties.containerClassName}>
      {shouldLoad ? (
        <ProgressiveImage src={src} alt={alt} {...properties} />
      ) : (
        <div
          className={cn(
            "bg-slate-100 animate-pulse",
            properties.containerClassName,
          )}
        />
      )}
    </div>
  );
}

// Avatar with fallback
interface AvatarProperties {
  src?: string;
  alt: string;
  fallback?: string;
  size?: "sm" | "md" | "lg" | "xl";
  className?: string;
}

export function Avatar({
  src,
  alt,
  fallback,
  size = "md",
  className,
}: AvatarProperties) {
  const [error, setError] = React.useState(false);

  const sizeClasses = {
    sm: "w-8 h-8 text-xs",
    md: "w-10 h-10 text-sm",
    lg: "w-14 h-14 text-base",
    xl: "w-20 h-20 text-lg",
  };

  const initials =
    fallback ||
    alt
      .split(" ")
      .map((n) => n[0])
      .join("")
      .toUpperCase()
      .slice(0, 2);

  return (
    <div
      className={cn(
        "rounded-full overflow-hidden bg-gradient-to-br from-primary-500 to-primary-600 flex items-center justify-center text-white font-bold",
        sizeClasses[size],
        className,
      )}
    >
      {src && !error ? (
        <img
          src={src}
          alt={alt}
          className="w-full h-full object-cover"
          onError={() => setError(true)}
        />
      ) : (
        <span>{initials}</span>
      )}
    </div>
  );
}

// Image grid with progressive loading
interface ImageGridProperties {
  images: { src: string; alt: string }[];
  columns?: 2 | 3 | 4;
  gap?: number;
  className?: string;
}

export function ImageGrid({
  images,
  columns = 3,
  gap = 4,
  className,
}: ImageGridProperties) {
  const colClasses = {
    2: "grid-cols-2",
    3: "grid-cols-3",
    4: "grid-cols-4",
  };

  return (
    <div className={cn("grid", colClasses[columns], `gap-${gap}`, className)}>
      {images.map((image, index) => (
        <LazyImage
          key={index}
          src={image.src}
          alt={image.alt}
          containerClassName="aspect-square rounded-lg"
        />
      ))}
    </div>
  );
}

export default ProgressiveImage;
