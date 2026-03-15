#!/bin/bash

# Semgrep Security Audit Script
# Usage: ./run-semgrep-audit.sh [security|quality|full|custom]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPORT_DIR="${SCRIPT_DIR}/audit-reports"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Create reports directory
mkdir -p "$REPORT_DIR"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_header() {
    echo -e "${BLUE}====================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}====================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Function to run Semgrep with specific configuration
run_semgrep() {
    local config="$1"
    local output_file="$2"
    local description="$3"
    
    print_header "Running: $description"
    
    if semgrep --config="$config" --json --output="$output_file" .; then
        print_success "Scan completed successfully"
        
        # Extract summary
        local findings=$(jq -r '.results | length' "$output_file" 2>/dev/null || echo "0")
        local rules=$(jq -r '.rules | length' "$output_file" 2>/dev/null || echo "0")
        
        echo "📊 Findings: $findings | Rules: $rules"
        
        if [ "$findings" -gt 0 ]; then
            print_warning "$findings issues found - check report for details"
        else
            print_success "No issues found!"
        fi
    else
        print_error "Scan failed"
        return 1
    fi
    
    echo ""
}

# Function to generate HTML report
generate_html_report() {
    local json_file="$1"
    local html_file="$2"
    
    cat > "$html_file" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Semgrep Security Audit Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background: #f5f5f5; padding: 20px; border-radius: 5px; }
        .finding { margin: 10px 0; padding: 10px; border-left: 4px solid #ccc; }
        .high { border-left-color: #d32f2f; background: #ffebee; }
        .medium { border-left-color: #f57c00; background: #fff3e0; }
        .low { border-left-color: #388e3c; background: #e8f5e8; }
        .code { background: #f5f5f5; padding: 5px; font-family: monospace; }
        .file-path { color: #666; font-size: 0.9em; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Semgrep Security Audit Report</h1>
        <p>Generated: $(date)</p>
    </div>
EOF
    
    if [ -f "$json_file" ] && command -v jq >/dev/null 2>&1; then
        jq -r '.results[] | 
            "<div class=\"finding \(.extra.severity // "unknown")\">
                <h3>\(.check_id)</h3>
                <p class=\"file-path\">\(.path):\(.start.line)</p>
                <p>\(.extra.message // "No message")</p>
                <pre class=\"code\">\(.lines // "No code snippet")</pre>
            </div>"' "$json_file" >> "$html_file"
    else
        echo "<p>Could not parse JSON file or jq not available</p>" >> "$html_file"
    fi
    
    cat >> "$html_file" << EOF
</body>
</html>
EOF
}

# Main execution
main() {
    print_header "Semgrep Security Audit Tool"
    echo "Report directory: $REPORT_DIR"
    echo "Timestamp: $TIMESTAMP"
    echo ""
    
    case "${1:-full}" in
        "security")
            print_header "Security-Focused Audit"
            
            run_semgrep "p/security-audit,p/secrets,p/sql-injection,p/command-injection,p/xss" \
                        "$REPORT_DIR/security-audit_$TIMESTAMP.json" \
                        "Security Rules (OWASP Top 10, Secrets, Injection)"
            
            generate_html_report "$REPORT_DIR/security-audit_$TIMESTAMP.json" \
                                "$REPORT_DIR/security-audit_$TIMESTAMP.html"
            
            print_success "Security report generated: $REPORT_DIR/security-audit_$TIMESTAMP.html"
            ;;
            
        "quality")
            print_header "Code Quality Audit"
            
            run_semgrep "p/bandit,p/flask,p/django" \
                        "$REPORT_DIR/quality-audit_$TIMESTAMP.json" \
                        "Code Quality Rules (Bandit, Flask, Django)"
            
            generate_html_report "$REPORT_DIR/quality-audit_$TIMESTAMP.json" \
                                "$REPORT_DIR/quality-audit_$TIMESTAMP.html"
            
            print_success "Quality report generated: $REPORT_DIR/quality-audit_$TIMESTAMP.html"
            ;;
            
        "full")
            print_header "Comprehensive Full Audit"
            
            # Security scan
            run_semgrep "p/security-audit,p/secrets,p/sql-injection,p/command-injection,p/xss" \
                        "$REPORT_DIR/security_$TIMESTAMP.json" \
                        "Security Rules"
            
            # Python security
            run_semgrep "p/bandit,p/flask,p/django,p/sql-injection" \
                        "$REPORT_DIR/python-security_$TIMESTAMP.json" \
                        "Python Security Rules"
            
            # Generate HTML reports
            generate_html_report "$REPORT_DIR/security_$TIMESTAMP.json" \
                                "$REPORT_DIR/security_$TIMESTAMP.html"
            generate_html_report "$REPORT_DIR/python-security_$TIMESTAMP.json" \
                                "$REPORT_DIR/python-security_$TIMESTAMP.html"
            
            # Create summary report
            cat > "$REPORT_DIR/summary_$TIMESTAMP.md" << EOF
# Semgrep Audit Summary

**Timestamp:** $(date)
**Scan Type:** Full Comprehensive Audit

## Security Scan Results
- Security Rules: $(jq -r '.results | length' "$REPORT_DIR/security_$TIMESTAMP.json" 2>/dev/null || echo "0") findings
- Python Security: $(jq -r '.results | length' "$REPORT_DIR/python-security_$TIMESTAMP.json" 2>/dev/null || echo "0") findings

## Reports Generated
- [Security HTML Report](security_$TIMESTAMP.html)
- [Python Security HTML Report](python-security_$TIMESTAMP.html)
- [Security JSON Data](security_$TIMESTAMP.json)
- [Python Security JSON Data](python-security_$TIMESTAMP.json)

## Quick Actions
1. Review high-severity findings first
2. Address security vulnerabilities immediately
3. Create tickets for medium/low priority issues
4. Update code to prevent future occurrences

---
*Generated by Semgrep Audit Script*
EOF
            
            print_success "Full audit completed!"
            print_success "Summary report: $REPORT_DIR/summary_$TIMESTAMP.md"
            print_success "HTML reports available in: $REPORT_DIR/"
            ;;
            
        "custom")
            if [ -z "$2" ]; then
                print_error "Custom scan requires configuration argument"
                echo "Usage: $0 custom \"p/security-audit,p/bandit\""
                exit 1
            fi
            
            run_semgrep "$2" \
                        "$REPORT_DIR/custom-audit_$TIMESTAMP.json" \
                        "Custom Configuration: $2"
            
            generate_html_report "$REPORT_DIR/custom-audit_$TIMESTAMP.json" \
                                "$REPORT_DIR/custom-audit_$TIMESTAMP.html"
            
            print_success "Custom audit completed: $REPORT_DIR/custom-audit_$TIMESTAMP.html"
            ;;
            
        *)
            echo "Usage: $0 [security|quality|full|custom]"
            echo ""
            echo "Options:"
            echo "  security  - Run security-focused audit"
            echo "  quality   - Run code quality audit"
            echo "  full      - Run comprehensive audit (default)"
            echo "  custom    - Run custom configuration"
            echo ""
            echo "Examples:"
            echo "  $0 security"
            echo "  $0 full"
            echo "  $0 custom \"p/secrets,p/sql-injection\""
            exit 1
            ;;
    esac
    
    print_header "Audit Complete"
    print_success "All reports saved to: $REPORT_DIR"
    echo ""
    echo "Latest Reports:"
    ls -la "$REPORT_DIR"/*"$TIMESTAMP"* 2>/dev/null || echo "No reports found"
}

# Check dependencies
if ! command -v semgrep >/dev/null 2>&1; then
    print_error "Semgrep not found. Please install it first:"
    echo "pip install semgrep"
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    print_warning "jq not found. HTML reports will be limited."
    echo "Install jq for better report generation: apt-get install jq"
fi

# Run main function with all arguments
main "$@"
