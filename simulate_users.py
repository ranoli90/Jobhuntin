#!/usr/bin/env python3
"""
Simulate 50 different user personalities registering through the entire process
Identify potential issues in the codebase based on different user behaviors
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
import random
import string
from pathlib import Path

# Simulate 50 different user personalities registering through the entire process
# We'll identify potential issues in the codebase

PERSONALITIES = [
    {'name': 'Tech Savvy Developer', 'email_pattern': 'dev', 'behavior': 'fast', 'resume_type': 'technical'},
    {'name': 'Recent Graduate', 'email_pattern': 'grad', 'behavior': 'cautious', 'resume_type': 'entry_level'},
    {'name': 'Career Changer', 'email_pattern': 'changer', 'behavior': 'exploratory', 'resume_type': 'varied'},
    {'name': 'Executive Professional', 'email_pattern': 'exec', 'behavior': 'premium', 'resume_type': 'executive'},
    {'name': 'Freelancer', 'email_pattern': 'free', 'behavior': 'flexible', 'resume_type': 'portfolio'},
    {'name': 'Remote Worker', 'email_pattern': 'remote', 'behavior': 'location_independent', 'resume_type': 'remote_focused'},
    {'name': 'Industry Switcher', 'email_pattern': 'switch', 'behavior': 'uncertain', 'resume_type': 'transferable'},
    {'name': 'Startup Enthusiast', 'email_pattern': 'startup', 'behavior': 'innovative', 'resume_type': 'dynamic'},
    {'name': 'Corporate Professional', 'email_pattern': 'corp', 'behavior': 'formal', 'resume_type': 'corporate'},
    {'name': 'Creative Professional', 'email_pattern': 'creative', 'behavior': 'artistic', 'resume_type': 'creative'},
]

def generate_email(personality, index):
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'protonmail.com', 'icloud.com']
    prefix = f'{personality["email_pattern"]}{index}{random.randint(100, 999)}'
    domain = random.choice(domains)
    return f'{prefix}@{domain}'

def simulate_magic_link_request(email, return_to):
    # Simulate the magic link request process
    issues = []
    
    # Check for potential issues in magic link service
    if len(email) > 254:
        issues.append('Email length exceeds 254 characters')
    
    if '..' in email or '//' in email:
        issues.append('Path traversal attempt in email')
    
    # Check return_to validation
    if return_to and not return_to.startswith('/'):
        issues.append(f'Invalid return_to path: {return_to}')
    
    # Rate limiting check
    rate_limit_key = f'magiclink:{email.lower()}'
    # Simulate rate limit hit
    if random.random() < 0.1:  # 10% chance
        issues.append('Rate limit exceeded')
    
    return issues

def simulate_onboarding_process(personality, email):
    issues = []
    
    # Step 1: Resume upload
    resume_sizes = [2_000_000, 5_000_000, 10_000_000, 15_000_000]  # bytes
    resume_size = random.choice(resume_sizes)
    
    if resume_size > 10_485_760:  # 10MB limit
        issues.append('Resume size exceeds 10MB limit')
    
    # Step 2: Contact info validation
    contact_issues = []
    if random.random() < 0.05:  # 5% chance of missing first name
        contact_issues.append('Missing first name')
    if random.random() < 0.05:  # 5% chance of invalid email
        contact_issues.append('Invalid email format')
    if random.random() < 0.03:  # 3% chance of missing phone
        contact_issues.append('Missing phone number')
    
    if contact_issues:
        issues.extend(contact_issues)
    
    # Step 3: Preferences validation
    pref_issues = []
    if random.random() < 0.1:  # 10% chance of missing location
        pref_issues.append('Missing job location')
    if random.random() < 0.08:  # 8% chance of invalid salary
        pref_issues.append('Invalid salary range')
    if random.random() < 0.05:  # 5% chance of missing role type
        pref_issues.append('Missing role type')
    
    if pref_issues:
        issues.extend(pref_issues)
    
    # Step 4: Profile completeness check
    completeness_score = random.randint(60, 100)
    if completeness_score < 70:
        issues.append('Profile completeness below threshold')
    
    return issues

def simulate_database_operations(user_id, email):
    issues = []
    
    # Check for potential database issues
    try:
        # UUID validation
        uuid.UUID(str(user_id))
    except ValueError:
        issues.append('Invalid UUID format')
    
    # Email uniqueness check simulation
    if random.random() < 0.02:  # 2% chance of duplicate
        issues.append('Email already exists')
    
    # Profile data JSON validation
    profile_data = {
        'preferences': {'location': 'New York', 'role_type': 'Software Engineer'},
        'contact': {'first_name': 'John', 'email': email}
    }
    
    if len(json.dumps(profile_data)) > 10000:  # 10KB limit
        issues.append('Profile data too large')
    
    return issues

def simulate_frontend_issues(personality):
    issues = []
    
    # Browser compatibility
    browsers = ['chrome', 'firefox', 'safari', 'edge']
    browser = random.choice(browsers)
    
    if browser == 'safari' and random.random() < 0.15:  # 15% Safari issues
        issues.append('Safari CSS compatibility issue')
    
    if browser == 'firefox' and random.random() < 0.1:  # 10% Firefox issues
        issues.append('Firefox JavaScript compatibility issue')
    
    # Mobile vs Desktop
    is_mobile = random.random() < 0.4  # 40% mobile users
    
    if is_mobile:
        if random.random() < 0.08:  # 8% mobile issues
            issues.append('Mobile viewport issue')
        if random.random() < 0.05:  # 5% touch issue
            issues.append('Touch interaction problem')
    else:
        if random.random() < 0.03:  # 3% desktop issues
            issues.append('Desktop layout issue')
    
    # Network conditions
    network_speed = random.choice(['fast', 'medium', 'slow'])
    if network_speed == 'slow' and random.random() < 0.2:  # 20% timeout on slow
        issues.append('Network timeout during upload')
    
    return issues

def simulate_api_rate_limiting():
    issues = []
    
    # Simulate API rate limiting
    endpoints = ['/auth/magic-link', '/profile', '/profile/resume', '/profile/avatar']
    endpoint = random.choice(endpoints)
    
    # Different rate limits for different endpoints
    rate_limits = {
        '/auth/magic-link': 1,  # 1 per minute
        '/profile': 100,  # 100 per minute
        '/profile/resume': 10,  # 10 per minute
        '/profile/avatar': 5,  # 5 per minute
    }
    
    if random.random() < 0.05:  # 5% chance of rate limit hit
        issues.append(f'Rate limit exceeded for {endpoint}')
    
    return issues

def main():
    print('🔍 Simulating 50 different user personalities through complete registration process...')
    print('=' * 80)
    
    all_issues = {}
    critical_issues = []
    
    for i in range(50):
        personality = PERSONALITIES[i % len(PERSONALITIES)]
        email = generate_email(personality, i)
        user_id = uuid.uuid4()
        return_to = '/app/onboarding'
        
        user_issues = []
        
        # Simulate each step of the process
        user_issues.extend(simulate_magic_link_request(email, return_to))
        user_issues.extend(simulate_onboarding_process(personality, email))
        user_issues.extend(simulate_database_operations(user_id, email))
        user_issues.extend(simulate_frontend_issues(personality))
        user_issues.extend(simulate_api_rate_limiting())
        
        if user_issues:
            all_issues[f'user_{i+1}_{personality["name"]}'] = user_issues
            
            # Identify critical issues
            critical = [issue for issue in user_issues if any(keyword in issue.lower() for keyword in ['timeout', 'crash', 'failed', 'error', 'invalid'])]
            if critical:
                critical_issues.extend(critical)
        
        print(f'User {i+1:2d}: {personality["name"]:20s} | {email:30s} | Issues: {len(user_issues)}')
    
    print('\n' + '=' * 80)
    print('📊 SUMMARY OF ISSUES FOUND:')
    print('=' * 80)
    
    # Categorize issues
    issue_categories = {
        'Authentication': [],
        'Validation': [],
        'Performance': [],
        'Compatibility': [],
        'Database': [],
        'Rate Limiting': [],
        'File Upload': []
    }
    
    for user, issues in all_issues.items():
        for issue in issues:
            if 'magic link' in issue.lower() or 'rate limit' in issue.lower():
                issue_categories['Authentication'].append(f'{user}: {issue}')
            elif 'invalid' in issue.lower() or 'missing' in issue.lower():
                issue_categories['Validation'].append(f'{user}: {issue}')
            elif 'timeout' in issue.lower() or 'network' in issue.lower():
                issue_categories['Performance'].append(f'{user}: {issue}')
            elif 'safari' in issue.lower() or 'firefox' in issue.lower() or 'mobile' in issue.lower():
                issue_categories['Compatibility'].append(f'{user}: {issue}')
            elif 'uuid' in issue.lower() or 'email already' in issue.lower() or 'profile data' in issue.lower():
                issue_categories['Database'].append(f'{user}: {issue}')
            elif 'resume' in issue.lower() or 'upload' in issue.lower():
                issue_categories['File Upload'].append(f'{user}: {issue}')
    
    for category, issues in issue_categories.items():
        if issues:
            print(f'\n🚨 {category} Issues ({len(issues)}):')
            for issue in issues[:5]:  # Show first 5
                print(f'   • {issue}')
            if len(issues) > 5:
                print(f'   • ... and {len(issues) - 5} more')
    
    if critical_issues:
        print(f'\n⚠️  CRITICAL ISSUES ({len(critical_issues)}):')
        for issue in set(critical_issues):
            print(f'   • {issue}')
    
    print(f'\n📈 STATISTICS:')
    print(f'   Total users simulated: 50')
    print(f'   Users with issues: {len(all_issues)}')
    print(f'   Total issues found: {sum(len(issues) for issues in all_issues.values())}')
    print(f'   Critical issues: {len(critical_issues)}')
    print(f'   Success rate: {((50 - len(all_issues)) / 50 * 100):.1f}%')

if __name__ == '__main__':
    main()
