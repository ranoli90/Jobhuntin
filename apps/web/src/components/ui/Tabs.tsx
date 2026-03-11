import React, { createContext, useContext, useState, useCallback } from "react";

type TabsContextValue = {
  value: string;
  onValueChange: (value: string) => void;
  tabsId: string;
};

const TabsContext = createContext<TabsContextValue | null>(null);

function useTabsContext() {
  const ctx = useContext(TabsContext);
  if (!ctx) {
    throw new Error("Tabs components must be used within a Tabs provider");
  }
  return ctx;
}

export const Tabs = ({
  children,
  className = "",
  value: controlledValue,
  defaultValue,
  onValueChange,
  ...properties
}: {
  children: React.ReactNode;
  className?: string;
  value?: string;
  defaultValue?: string;
  onValueChange?: (value: string) => void;
  [key: string]: unknown;
}) => {
  const [internalValue, setInternalValue] = useState(defaultValue ?? "");
  const isControlled = controlledValue !== undefined;
  const value = isControlled ? controlledValue : internalValue;

  const handleValueChange = useCallback(
    (newValue: string) => {
      if (!isControlled) {
        setInternalValue(newValue);
      }
      onValueChange?.(newValue);
    },
    [isControlled, onValueChange]
  );

  const tabsId = React.useId();

  return (
    <TabsContext.Provider
      value={{
        value,
        onValueChange: handleValueChange,
        tabsId,
      }}
    >
      <div className={`${className}`} {...properties}>
        {children}
      </div>
    </TabsContext.Provider>
  );
};

export const TabsList = ({
  children,
  className = "",
}: {
  children: React.ReactNode;
  className?: string;
}) => (
  <div
    className={`flex gap-1 border-b border-slate-200 mb-4 ${className}`}
    role="tablist"
  >
    {children}
  </div>
);

export const TabsTrigger = ({
  children,
  value,
  className = "",
  ...props
}: {
  children: React.ReactNode;
  value: string;
  className?: string;
} & Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "value">) => {
  const { value: activeValue, onValueChange, tabsId } = useTabsContext();
  const isSelected = value === activeValue;
  const triggerId = `${tabsId}-trigger-${value}`;

  return (
    <button
      type="button"
      role="tab"
      aria-selected={isSelected}
      id={triggerId}
      aria-controls={`${tabsId}-content-${value}`}
      tabIndex={isSelected ? 0 : -1}
      className={`px-3 py-2 text-sm font-medium text-slate-600 hover:text-slate-900 border-b-2 transition-colors ${
        isSelected ? "border-slate-900 text-slate-900" : "border-transparent hover:border-slate-300"
      } ${className}`}
      data-value={value}
      onClick={() => onValueChange(value)}
      {...props}
    >
      {children}
    </button>
  );
};

export const TabsContent = ({
  children,
  value,
  className = "",
  ...props
}: {
  children: React.ReactNode;
  value: string;
  className?: string;
} & React.HTMLAttributes<HTMLDivElement>) => {
  const { value: activeValue, tabsId } = useTabsContext();
  const triggerId = `${tabsId}-trigger-${value}`;
  const contentId = `${tabsId}-content-${value}`;

  if (value !== activeValue) {
    return null;
  }

  return (
    <div
      role="tabpanel"
      id={contentId}
      aria-labelledby={triggerId}
      className={`${className}`}
      data-value={value}
      {...props}
    >
      {children}
    </div>
  );
};
