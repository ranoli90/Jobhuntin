#!/usr/bin/env python3
"""
Second simulation with 50 different user personalities
Focus on edge cases, stress testing, and real-world scenarios
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
import random
import string
from pathlib import Path

# Enhanced personality profiles with more edge cases
PERSONALITIES = [
    {'name': 'Senior Developer', 'email_pattern': 'senior', 'behavior': 'experienced', 'resume_type': 'technical', 'age_range': '35-45'},
    {'name': 'College Student', 'email_pattern': 'student', 'behavior': 'inexperienced', 'resume_type': 'entry_level', 'age_range': '18-22'},
    {'name': 'Career Returner', 'email_pattern': 'returner', 'behavior': 'cautious', 'resume_type': 'varied', 'age_range': '45-55'},
    {'name': 'International Applicant', 'email_pattern': 'intl', 'behavior': 'language_barrier', 'resume_type': 'multilingual', 'age_range': '25-35'},
    {'name': 'Non-Traditional Background', 'email_pattern': 'nontrad', 'behavior': 'unconventional', 'resume_type': 'creative', 'age_range': '30-40'},
    {'name': 'Veteran', 'email_pattern': 'veteran', 'behavior': 'structured', 'resume_type': 'military', 'age_range': '40-50'},
    {'name': 'Gig Economy Worker', 'email_pattern': 'gig', 'behavior': 'flexible', 'resume_type': 'portfolio', 'age_range': '25-35'},
    {'name': 'Academic Researcher', 'email_pattern': 'academic', 'behavior': 'detailed', 'resume_type': 'academic', 'age_range': '30-45'},
    {'name': 'Sales Professional', 'email_pattern': 'sales', 'behavior': 'persuasive', 'resume_type': 'sales', 'age_range': '28-38'},
    {'name': 'Healthcare Worker', 'email_pattern': 'health', 'behavior': 'caring', 'resume_type': 'healthcare', 'age_range': '25-40'},
    {'name': 'Teacher', 'email_pattern': 'teacher', 'behavior': 'educational', 'resume_type': 'teaching', 'age_range': '30-50'},
    {'name': 'Consultant', 'email_pattern': 'consultant', 'behavior': 'analytical', 'resume_type': 'consulting', 'age_range': '35-50'},
    {'name': 'Startup Founder', 'email_pattern': 'founder', 'behavior': 'entrepreneurial', 'resume_type': 'founder', 'age_range': '25-40'},
    {'name': 'Government Employee', 'email_pattern': 'gov', 'behavior': 'bureaucratic', 'resume_type': 'government', 'age_range': '35-55'},
    {'name': 'Freelance Designer', 'email_pattern': 'designer', 'behavior': 'creative', 'resume_type': 'design', 'age_range': '24-35'},
    {'name': 'Data Scientist', 'email_pattern': 'data', 'behavior': 'analytical', 'resume_type': 'technical', 'age_range': '28-38'},
    {'name': 'Marketing Manager', 'email_pattern': 'marketing', 'behavior': 'strategic', 'resume_type': 'marketing', 'age_range': '30-45'},
    {'name': 'HR Professional', 'email_pattern': 'hr', 'behavior': 'people_focused', 'resume_type': 'hr', 'age_range': '32-48'},
    {'name': 'Engineer', 'email_pattern': 'engineer', 'behavior': 'technical', 'resume_type': 'engineering', 'age_range': '26-42'},
]

def generate_complex_email(personality, index):
    """Generate more complex email scenarios"""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'protonmail.com', 'icloud.com', 'aol.com', 'mail.com']
    
    # Add edge cases
    if personality['name'] == 'International Applicant':
        # International domains
        international_domains = ['yahoo.co.uk', 'gmail.co.in', 'outlook.com.au', 'hotmail.ca']
        prefix = f'{personality["email_pattern"]}{index}{random.randint(100, 999)}'
        domain = random.choice(international_domains)
        return f'{prefix}@{domain}'
    
    if personality['name'] == 'Non-Traditional Background':
        # Unusual email formats
        prefixes = [f'{personality["email_pattern"]}.{random.choice(["creative", "artist", "designer"])}{index}',
                     f'{random.choice(["the", "real", "official"])}_{personality["email_pattern"]}{index}']
        prefix = random.choice(prefixes)
        domain = random.choice(domains)
        return f'{prefix}@{domain}'
    
    # Standard case
    prefix = f'{personality["email_pattern"]}{index}{random.randint(100, 999)}'
    domain = random.choice(domains)
    return f'{prefix}@{domain}'

def simulate_edge_case_magic_link(email, return_to, personality):
    """Simulate edge cases in magic link process"""
    issues = []
    
    # Edge case 1: Very long email
    if len(email) > 300:
        issues.append('Email length exceeds 300 characters')
    
    # Edge case 2: Special characters in email
    if any(char in email for char in ['+', '-', '_', '.']) and random.random() < 0.3:
        issues.append('Special characters in email causing validation issues')
    
    # Edge case 3: Unicode characters
    if personality['name'] == 'International Applicant' and random.random() < 0.4:
        issues.append('Unicode characters in email causing encoding issues')
    
    # Edge case 4: Return to path manipulation
    if return_to and random.random() < 0.2:
        # Try to inject malicious paths
        malicious_paths = ['../../../etc/passwd', 'javascript:alert(1)', 'data:text/html,<script>']
        issues.append(f'Path injection attempt: {random.choice(malicious_paths)}')
    
    # Edge case 5: Concurrent requests
    if random.random() < 0.15:  # 15% chance of concurrent requests
        issues.append('Concurrent magic link requests causing race condition')
    
    # Edge case 6: Expired token scenario
    if random.random() < 0.1:
        issues.append('Magic link token expired before user click')
    
    return issues

def simulate_complex_onboarding(personality, email):
    """Simulate complex onboarding scenarios"""
    issues = []
    
    # Edge case 1: Multiple file uploads
    if personality['name'] in ['Freelance Designer', 'Portfolio-based roles'] and random.random() < 0.3:
        issues.append('Multiple resume files uploaded causing confusion')
    
    # Edge case 2: Very large files
    if personality['name'] in ['Academic Researcher', 'Senior Developer'] and random.random() < 0.4:
        large_sizes = [20_000_000, 25_000_000, 30_000_000]  # 20-30MB
        if random.choice(large_sizes) > 15_728_640:  # 15MB limit
            issues.append('Resume size exceeds new 15MB limit')
    
    # Edge case 3: Corrupted files
    if random.random() < 0.05:  # 5% chance
        issues.append('Corrupted PDF file causing parsing failure')
    
    # Edge case 4: Missing critical information
    critical_fields = ['first_name', 'email', 'location', 'role_type']
    missing_count = random.randint(0, 3)
    if missing_count > 0:
        missing = random.sample(critical_fields, missing_count)
        for field in missing:
            issues.append(f'Missing critical field: {field}')
    
    # Edge case 5: Invalid data formats
    if personality['name'] == 'International Applicant' and random.random() < 0.3:
        issues.append('International phone number format not recognized')
    
    # Edge case 6: Salary expectations out of range
    if personality['name'] in ['Senior Developer', 'Consultant'] and random.random() < 0.2:
        issues.append('Salary expectation outside reasonable range ($500k+)')
    
    # Edge case 7: Special characters in names
    if personality['name'] == 'International Applicant' and random.random() < 0.25:
        issues.append('Special characters in name causing database issues')
    
    # Edge case 8: LinkedIn URL validation
    if random.random() < 0.15:  # 15% chance
        invalid_urls = ['not-a-url', 'http://invalid', 'https://broken.link', '']
        issues.append(f'Invalid LinkedIn URL: {random.choice(invalid_urls)}')
    
    # Edge case 9: Session timeout during onboarding
    if random.random() < 0.08:  # 8% chance
        issues.append('Session timeout during long onboarding process')
    
    # Edge case 10: Browser compatibility issues
    browser_issues = {
        'Safari': ['CSS Grid not supported', 'Flexbox gap not supported', 'Backdrop filter not supported'],
        'Firefox': ['CSS custom properties not supported', 'JavaScript ES6+ features not supported'],
        'IE': ['Modern JavaScript not supported', 'CSS Grid not supported'],
        'Mobile Safari': ['Viewport issues', 'Touch event problems']
    }
    
    browser = random.choice(list(browser_issues.keys()))
    if random.random() < 0.2:  # 20% chance
        issues.append(f'{browser} compatibility: {random.choice(browser_issues[browser])}')
    
    return issues

def simulate_database_edge_cases(user_id, email, personality):
    """Simulate database edge cases"""
    issues = []
    
    # Edge case 1: UUID collisions (extremely rare but possible)
    if random.random() < 0.001:  # 0.1% chance
        issues.append('UUID collision detected')
    
    # Edge case 2: Email case sensitivity issues
    if email.lower() != email and random.random() < 0.1:
        issues.append('Email case sensitivity causing duplicate detection')
    
    # Edge case 3: Profile data size limits
    if personality['name'] in ['Academic Researcher', 'Senior Developer'] and random.random() < 0.3:
            # Large profile data
            profile_data = {
                'preferences': {'location': 'New York', 'role_type': 'Software Engineer'},
                'contact': {'first_name': 'John', 'email': email},
                'experience': [{'title': f'Job {i}', 'description': 'A' * 1000} for i in range(100)],
                'skills': [f'Skill {i}' for i in range(500)]
            }
            
            if len(json.dumps(profile_data)) > 50000:  # 50KB limit
                issues.append('Profile data exceeds size limit')
    
    # Edge case 4: Concurrent profile updates
    if random.random() < 0.1:  # 10% chance
        issues.append('Concurrent profile updates causing data inconsistency')
    
    # Edge case 5: Database connection issues
    if random.random() < 0.05:  # 5% chance
        issues.append('Database connection timeout during profile save')
    
    # Edge case 6: Transaction rollback
    if random.random() < 0.03:  # 3% chance
        issues.append('Transaction rollback due to constraint violation')
    
    # Edge case 7: Foreign key constraint issues
    if random.random() < 0.02:  # 2% chance
        issues.append('Foreign key constraint violation')
    
    return issues

def simulate_api_stress_testing():
    """Simulate API stress testing scenarios"""
    issues = []
    
    # Edge case 1: API rate limiting under stress
    endpoints = ['/auth/magic-link', '/profile', '/profile/resume', '/profile/avatar', '/profile/preferences']
    
    # Simulate high traffic
    if random.random() < 0.2:  # 20% chance
        endpoint = random.choice(endpoints)
        issues.append(f'API rate limit exceeded under stress for {endpoint}')
    
    # Edge case 2: Memory exhaustion
    if random.random() < 0.05:  # 5% chance
        issues.append('API server memory exhaustion during high load')
    
    # Edge case 3: Database connection pool exhaustion
    if random.random() < 0.08:  # 8% chance
        issues.append('Database connection pool exhausted')
    
    # Edge case 4: File storage quota exceeded
    if random.random() < 0.03:  # 3% chance
        issues.append('File storage quota exceeded')
    
    # Edge case 5: Email service rate limiting
    if random.random() < 0.15:  # 15% chance
        issues.append('Email service (Resend) rate limiting triggered')
    
    # Edge case 6: CDN/Static file issues
    if random.random() < 0.04:  # 4% chance
        issues.append('CDN static file delivery failure')
    
    return issues

def simulate_security_scenarios():
    """Simulate security-related edge cases"""
    issues = []
    
    # Edge case 1: SQL injection attempts
    if random.random() < 0.02:  # 2% chance
        issues.append('SQL injection attempt detected and blocked')
    
    # Edge case 2: XSS attempts
    if random.random() < 0.03:  # 3% chance
        issues.append('XSS attempt detected and sanitized')
    
    # Edge case 3: CSRF attempts
    if random.random() < 0.01:  # 1% chance
        issues.append('CSRF token validation failed')
    
    # Edge case 4: Brute force attempts
    if random.random() < 0.05:  # 5% chance
        issues.append('Multiple failed login attempts detected')
    
    # Edge case 5: Suspicious activity patterns
    if random.random() < 0.02:  # 2% chance
        issues.append('Suspicious activity pattern detected')
    
    return issues

def simulate_network_conditions():
    """Simulate various network conditions"""
    issues = []
    
    # Edge case 1: Very slow network
    if random.random() < 0.1:  # 10% chance
        issues.append('Very slow network connection causing timeouts')
    
    # Edge case 2: Intermittent connection
    if random.random() < 0.08:  # 8% chance
        issues.append('Intermittent network connection')
    
    # Edge case 3: DNS resolution issues
    if random.random() < 0.03:  # 3% chance
        issues.append('DNS resolution failure')
    
    # Edge case 4: Proxy/VPN issues
    if random.random() < 0.05:  # 5% chance
        issues.append('Proxy/VPN blocking API requests')
    
    # Edge case 5: Mobile network issues
    if random.random() < 0.12:  # 12% chance
        issues.append('Mobile network instability')
    
    return issues

def main():
    print('🔍 SIMULATION V2: 50 Complex User Personalities with Edge Cases')
    print('=' * 80)
    
    all_issues = {}
    critical_issues = []
    security_issues = []
    
    for i in range(50):
        personality = PERSONALITIES[i % len(PERSONALITIES)]
        email = generate_complex_email(personality, i)
        user_id = uuid.uuid4()
        return_to = '/app/onboarding'
        
        user_issues = []
        
        # Simulate each step with edge cases
        user_issues.extend(simulate_edge_case_magic_link(email, return_to, personality))
        user_issues.extend(simulate_complex_onboarding(personality, email))
        user_issues.extend(simulate_database_edge_cases(user_id, email, personality))
        user_issues.extend(simulate_api_stress_testing())
        user_issues.extend(simulate_security_scenarios())
        user_issues.extend(simulate_network_conditions())
        
        if user_issues:
            all_issues[f'user_{i+1}_{personality["name"]}'] = user_issues
            
            # Identify critical issues
            critical = [issue for issue in user_issues if any(keyword in issue.lower() for keyword in ['timeout', 'crash', 'failed', 'error', 'invalid', 'corrupted', 'exceeded'])]
            if critical:
                critical_issues.extend(critical)
            
            # Identify security issues
            security = [issue for issue in user_issues if any(keyword in issue.lower() for keyword in ['injection', 'xss', 'csrf', 'brute force', 'suspicious'])]
            if security:
                security_issues.extend(security)
        
        print(f'User {i+1:2d}: {personality["name"]:25s} | {personality["age_range"]:8s} | {email:35s} | Issues: {len(user_issues)}')
    
    print('\n' + '=' * 80)
    print('📊 SIMULATION V2 RESULTS:')
    print('=' * 80)
    
    # Categorize issues
    issue_categories = {
        'Authentication': [],
        'Validation': [],
        'Performance': [],
        'Compatibility': [],
        'Database': [],
        'Security': [],
        'File Upload': [],
        'Network': [],
        'API Stress': []
    }
    
    for user, issues in all_issues.items():
        for issue in issues:
            if any(keyword in issue.lower() for keyword in ['magic link', 'rate limit', 'token', 'session']):
                issue_categories['Authentication'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['invalid', 'missing', 'corrupted']):
                issue_categories['Validation'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['timeout', 'slow', 'memory', 'connection']):
                issue_categories['Performance'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['safari', 'firefox', 'ie', 'mobile']):
                issue_categories['Compatibility'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['database', 'transaction', 'constraint']):
                issue_categories['Database'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['injection', 'xss', 'csrf', 'brute force']):
                issue_categories['Security'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['resume', 'upload', 'file']):
                issue_categories['File Upload'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['network', 'dns', 'proxy']):
                issue_categories['Network'].append(f'{user}: {issue}')
            elif any(keyword in issue.lower() for keyword in ['api', 'rate limit', 'quota']):
                issue_categories['API Stress'].append(f'{user}: {issue}')
    
    for category, issues in issue_categories.items():
        if issues:
            print(f'\n🚨 {category} Issues ({len(issues)}):')
            for issue in issues[:3]:  # Show first 3
                print(f'   • {issue}')
            if len(issues) > 3:
                print(f'   • ... and {len(issues) - 3} more')
    
    if critical_issues:
        print(f'\n⚠️  CRITICAL ISSUES ({len(critical_issues)}):')
        for issue in set(critical_issues):
            print(f'   • {issue}')
    
    if security_issues:
        print(f'\n🔒 SECURITY ISSUES ({len(security_issues)}):')
        for issue in set(security_issues):
            print(f'   • {issue}')
    
    print(f'\n📈 V2 STATISTICS:')
    print(f'   Total users simulated: 50')
    print(f'   Users with issues: {len(all_issues)}')
    print(f'   Total issues found: {sum(len(issues) for issues in all_issues.values())}')
    print(f'   Critical issues: {len(critical_issues)}')
    print(f'   Security issues: {len(security_issues)}')
    print(f'   Success rate: {((50 - len(all_issues)) / 50 * 100):.1f}%')
    
    # Compare with previous simulation
    print(f'\n🔄 COMPARISON WITH V1:')
    print(f'   V1 Success Rate: 26.0%')
    print(f'   V2 Success Rate: {((50 - len(all_issues)) / 50 * 100):.1f}%')
    improvement = ((50 - len(all_issues)) / 50 * 100) - 26.0
    print(f'   Change: {improvement:+.1f}%')
    
    # Personality analysis
    print(f'\n👥 PERSONALITY ANALYSIS:')
    personality_issues = {}
    for user, issues in all_issues.items():
        personality = user.split('_')[2:]
        personality_key = ' '.join(personality)
        if personality_key not in personality_issues:
            personality_issues[personality_key] = []
        personality_issues[personality_key].extend(issues)
    
    avg_issues = {k: len(v) for k, v in personality_issues.items()}
    worst_personalities = sorted(avg_issues.items(), key=lambda x: x[1], reverse=True)
    
    print(f'   Most affected personalities:')
    for personality, count in worst_personalities[:5]:
        print(f'   • {personality}: {count} issues')

if __name__ == '__main__':
    main()
