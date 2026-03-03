import * as React from "react";
import { Input } from "./Input";
import { cn } from "../../lib/utils";
import { useDebounce } from "../../lib/debounce";

interface AutoCompleteInputProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'onChange'> {
  icon?: React.ReactNode;
  placeholder?: string;
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
  suggestions: string[];
  maxSuggestions?: number;
  className?: string;
  error?: boolean;
  debounceMs?: number; // New prop for debounce timing
  enableCache?: boolean; // New prop for caching
}

export function AutoCompleteInput({
  icon,
  placeholder,
  value,
  onChange,
  onClear,
  suggestions,
  maxSuggestions = 5,
  className,
  error,
  debounceMs = 150, // Default 150ms debounce
  enableCache = true, // Enable caching by default
  ...props
}: AutoCompleteInputProps) {
  const [isOpen, setIsOpen] = React.useState(false);
  const [highlightedIndex, setHighlightedIndex] = React.useState(-1);
  const [localValue, setLocalValue] = React.useState(value);
  const inputRef = React.useRef<HTMLInputElement>(null);
  const listRef = React.useRef<HTMLUListElement>(null);
  
  // Cache for filtered suggestions to avoid re-filtering same inputs
  const cacheRef = React.useRef<Map<string, string[]>>(new Map());
  
  // Sync local value with prop value
  React.useEffect(() => {
    setLocalValue(value);
  }, [value]);
  
  // Debounced change handler
  const debouncedOnChange = useDebounce(
    React.useCallback((newValue: string) => {
      onChange(newValue);
    }, [onChange]),
    debounceMs,
    [onChange, debounceMs]
  );

  const filteredSuggestions = React.useMemo(() => {
    if (!localValue.trim()) return [];
    
    // Check cache first if enabled
    if (enableCache) {
      const cacheKey = `${localValue.toLowerCase()}_${suggestions.length}`;
      const cached = cacheRef.current.get(cacheKey);
      if (cached) {
        return cached.slice(0, maxSuggestions);
      }
    }
    
    // Filter suggestions
    const filtered = suggestions
      .filter(suggestion =>
        suggestion.toLowerCase().includes(localValue.toLowerCase())
      )
      .slice(0, maxSuggestions);
    
    // Cache result if enabled
    if (enableCache) {
      const cacheKey = `${localValue.toLowerCase()}_${suggestions.length}`;
      cacheRef.current.set(cacheKey, filtered);
      
      // Limit cache size to prevent memory leaks
      if (cacheRef.current.size > 100) {
        const firstKey = cacheRef.current.keys().next().value;
        if (firstKey) {
          cacheRef.current.delete(firstKey);
        }
      }
    }
    
    return filtered;
  }, [suggestions, localValue, maxSuggestions, enableCache]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue); // Update local value immediately for responsive UI
    
    // Debounce the onChange callback
    debouncedOnChange(newValue);
    
    // Update dropdown visibility based on local value
    setIsOpen(newValue.length > 0 && filteredSuggestions.length > 0);
    setHighlightedIndex(-1);
  };

  const handleInputFocus = () => {
    if (localValue && filteredSuggestions.length > 0) {
      setIsOpen(true);
    }
  };

  const handleInputBlur = () => {
    // Delay closing to allow click on suggestions
    setTimeout(() => setIsOpen(false), 150);
  };

  const handleSuggestionClick = (suggestion: string) => {
    setLocalValue(suggestion);
    onChange(suggestion); // Immediate update for selection
    setIsOpen(false);
    setHighlightedIndex(-1);
    inputRef.current?.focus();
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || filteredSuggestions.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev < filteredSuggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setHighlightedIndex(prev =>
          prev > 0 ? prev - 1 : filteredSuggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault();
        if (highlightedIndex >= 0) {
          handleSuggestionClick(filteredSuggestions[highlightedIndex]);
        }
        break;
      case 'Escape':
        setIsOpen(false);
        setHighlightedIndex(-1);
        break;
    }
  };

  React.useEffect(() => {
    if (highlightedIndex >= 0 && listRef.current) {
      const highlightedElement = listRef.current.children[highlightedIndex] as HTMLElement;
      highlightedElement?.scrollIntoView({ block: 'nearest' });
    }
  }, [highlightedIndex]);

  return (
    <div className="relative">
      <Input
        ref={inputRef}
        icon={icon}
        type="text"
        placeholder={placeholder}
        value={localValue}
        onChange={handleInputChange}
        onFocus={handleInputFocus}
        onBlur={handleInputBlur}
        onKeyDown={handleKeyDown}
        onClear={onClear}
        className={cn(className)}
        error={error}
        autoComplete="off"
        role="combobox"
        aria-expanded={isOpen}
        aria-autocomplete="list"
        aria-controls="autocomplete-listbox"
        {...props}
      />
      {isOpen && filteredSuggestions.length > 0 && (
        <ul
          ref={listRef}
          id="autocomplete-listbox"
          role="listbox"
          className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-48 overflow-y-auto"
        >
          {filteredSuggestions.map((suggestion, index) => (
            <li
              key={suggestion}
              role="option"
              aria-selected={index === highlightedIndex}
              className={cn(
                "px-3 py-2 text-sm cursor-pointer hover:bg-slate-50",
                index === highlightedIndex && "bg-slate-50"
              )}
              onMouseDown={() => handleSuggestionClick(suggestion)}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              {suggestion}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
