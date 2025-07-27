#!/usr/bin/env python3
"""
Dependency Fix Script for InsureMyWay Web Application
This script helps diagnose and fix common dependency issues, particularly with PIL/Pillow and ReportLab.
"""

import subprocess
import sys
import os
import importlib

def run_command(command, description):
    """Run a command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout:
                print(f"Output: {result.stdout.strip()}")
            return True
        else:
            print(f"❌ Failed: {description}")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Exception during {description}: {e}")
        return False

def check_import(module_name):
    """Check if a module can be imported"""
    try:
        importlib.import_module(module_name)
        print(f"✅ {module_name} - OK")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - FAILED: {e}")
        return False

def main():
    print("🚀 InsureMyWay Dependency Fix Script")
    print("=" * 50)
    
    # Check current Python version
    print(f"🐍 Python Version: {sys.version}")
    print(f"📁 Current Directory: {os.getcwd()}")
    
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️ Not in a virtual environment - consider activating venv")
    
    print("\n" + "=" * 50)
    print("📋 STEP 1: Checking Current Dependencies")
    print("=" * 50)
    
    # Check current imports
    modules_to_check = [
        'flask',
        'flask_sqlalchemy',
        'flask_bcrypt',
        'PIL',
        'reportlab',
        'reportlab.pdfgen.canvas'
    ]
    
    failed_modules = []
    for module in modules_to_check:
        if not check_import(module):
            failed_modules.append(module)
    
    if not failed_modules:
        print("\n🎉 All dependencies are working correctly!")
        return
    
    print(f"\n⚠️ Found {len(failed_modules)} problematic modules: {', '.join(failed_modules)}")
    
    print("\n" + "=" * 50)
    print("🔧 STEP 2: Fixing Dependencies")
    print("=" * 50)
    
    # Fix PIL/Pillow issues
    if any('PIL' in module for module in failed_modules):
        print("\n🔧 Fixing PIL/Pillow Issues...")
        
        # Method 1: Uninstall and reinstall Pillow
        run_command("pip uninstall Pillow -y", "Uninstalling corrupted Pillow")
        run_command("pip cache purge", "Clearing pip cache")
        run_command("pip install Pillow", "Reinstalling Pillow")
        
        # Check if it worked
        if check_import('PIL'):
            print("✅ PIL/Pillow fixed successfully!")
        else:
            print("⚠️ Trying alternative Pillow installation...")
            run_command("pip install --force-reinstall --no-cache-dir Pillow==10.0.1", "Force reinstalling specific Pillow version")
    
    # Fix ReportLab issues
    if any('reportlab' in module for module in failed_modules):
        print("\n🔧 Fixing ReportLab Issues...")
        
        run_command("pip uninstall reportlab -y", "Uninstalling ReportLab")
        run_command("pip install reportlab", "Reinstalling ReportLab")
        
        # Check if it worked
        if check_import('reportlab'):
            print("✅ ReportLab fixed successfully!")
    
    print("\n" + "=" * 50)
    print("✅ STEP 3: Final Verification")
    print("=" * 50)
    
    # Final check
    all_working = True
    for module in modules_to_check:
        if not check_import(module):
            all_working = False
    
    if all_working:
        print("\n🎉 All dependencies are now working correctly!")
        print("✅ You can now run: python app.py")
    else:
        print("\n⚠️ Some issues remain. Try these manual steps:")
        print("1. pip uninstall Pillow reportlab -y")
        print("2. pip cache purge")
        print("3. pip install --upgrade pip")
        print("4. pip install Pillow reportlab")
        print("5. If still failing, try: pip install --force-reinstall --no-cache-dir Pillow reportlab")
    
    print("\n" + "=" * 50)
    print("📋 Alternative Solutions")
    print("=" * 50)
    print("If dependencies still fail:")
    print("1. ✅ The app has been modified to work without PDF generation")
    print("2. ✅ PDF download buttons will show error messages instead of crashing")
    print("3. ✅ All other features will work normally")
    print("4. 🔧 To fix PDF generation later, reinstall: pip install Pillow reportlab")

if __name__ == "__main__":
    main()
