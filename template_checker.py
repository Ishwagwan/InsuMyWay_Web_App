#!/usr/bin/env python3
"""
Template Checker for InsuMyWay Web Application
This script checks all templates for common issues and validates their structure.
"""

import os
import re
from pathlib import Path

def check_template_syntax(template_path):
    """Check template for common syntax issues"""
    issues = []
    
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for unclosed tags
        open_tags = re.findall(r'<(\w+)[^>]*>', content)
        close_tags = re.findall(r'</(\w+)>', content)
        
        # Check for missing closing tags (basic check)
        for tag in ['html', 'head', 'body', 'div', 'form', 'table']:
            open_count = content.count(f'<{tag}')
            close_count = content.count(f'</{tag}>')
            if open_count != close_count:
                issues.append(f"Mismatched {tag} tags: {open_count} open, {close_count} close")
        
        # Check for Flask template syntax
        if '{{' in content and '}}' not in content:
            issues.append("Unclosed Flask template variable")
        if '{%' in content and '%}' not in content:
            issues.append("Unclosed Flask template block")
            
        # Check for common CSS/JS issues
        if 'href=""' in content or 'src=""' in content:
            issues.append("Empty href or src attributes found")
            
        # Check for missing base template extension
        if template_path.name != 'base.html' and '{% extends' not in content:
            issues.append("Template doesn't extend base template")
            
    except Exception as e:
        issues.append(f"Error reading file: {str(e)}")
        
    return issues

def main():
    """Main function to check all templates"""
    templates_dir = Path('templates')
    
    if not templates_dir.exists():
        print("❌ Templates directory not found!")
        return
        
    print("🔍 InsuMyWay Template Checker")
    print("=" * 50)
    
    template_files = list(templates_dir.glob('*.html'))
    total_issues = 0
    
    for template_file in sorted(template_files):
        print(f"\n📄 Checking: {template_file.name}")
        issues = check_template_syntax(template_file)
        
        if issues:
            total_issues += len(issues)
            print(f"   ⚠️  Found {len(issues)} issue(s):")
            for issue in issues:
                print(f"      - {issue}")
        else:
            print("   ✅ No issues found")
    
    print(f"\n" + "=" * 50)
    print(f"📊 Summary: {total_issues} total issues found across {len(template_files)} templates")
    
    if total_issues == 0:
        print("🎉 All templates passed basic validation!")
    else:
        print("⚠️  Some templates need attention.")

if __name__ == "__main__":
    main()
