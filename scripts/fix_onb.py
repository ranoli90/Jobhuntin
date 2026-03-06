import re

file_path = "apps/web/src/pages/app/Onboarding.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# Fix 1: setStepLoadingStates unused assignment
content = content.replace(
    "const [stepLoadingStates] = React.useState<Record<string, boolean>>({});",
    "const stepLoadingStates: Record<string, boolean> = {};",
)

# Fix 2: window -> globalThis
content = re.sub(r"\bwindow\.", "globalThis.", content)

# Fix 3: parseInt -> Number.parseInt
content = re.sub(r"(?<!\.)\bparseInt\(", "Number.parseInt(", content)

# Fix 4: isNaN -> Number.isNaN
content = re.sub(r"(?<!\.)\bisNaN\(", "Number.isNaN(", content)

# Fix 5: Nested ternaries for network errors
network_err_pattern = r"""\s*const message = isNetworkError\s*\n\s*\?\s*"Network error\. Please check your connection and try again\."\s*\n\s*:\s*\(typeof \(err as Error\)\.message === 'string' && !err\.message\.includes\('\[object'\)\)\s*\?\s*err\.message\s*:\s*([^;]+);"""

replacement = """
      let message = \\1;
      if (isNetworkError) {
        message = "Network error. Please check your connection and try again.";
      } else if (typeof (err as Error).message === 'string' && !err.message.includes('[object')) {
        message = err.message;
      }"""

content = re.sub(network_err_pattern, replacement, content)

# Fix 6: Nested ternaries for non-network errors (handleComplete, handleSaveWorkStyle)
simple_err_pattern = r"""\s*const message = \(typeof \(err as Error\)\.message === 'string' && !err\.message\.includes\('\[object'\)\)\s*\?\s*err\.message\s*:\s*([^;]+);"""

replacement2 = """
      let message = \\1;
      if (typeof (err as Error).message === 'string' && !err.message.includes('[object')) {
        message = err.message;
      }"""

content = re.sub(simple_err_pattern, replacement2, content)

# For any case where err doesn't get coerced to `err as Error` (err.message)
err_message_pattern = r"""\s*const message = \(typeof err\.message === 'string' && !err\.message\.includes\('\[object'\)\)\s*\?\s*err\.message\s*:\s*([^;]+);"""
replacement3 = """
      let message = \\1;
      if (typeof err.message === 'string' && !err.message.includes('[object')) {
        message = err.message;
      }"""
content = re.sub(err_message_pattern, replacement3, content)

# Fix progress tags
content = content.replace(
    'role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}',
    "/* using native progress */",
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Applied fixes to Onboarding.tsx")
