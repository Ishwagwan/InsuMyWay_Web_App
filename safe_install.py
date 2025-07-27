#!/usr/bin/env python3
"""
Safe Installation Script for InsureMyWay Web Application
This script handles pip process locks and installs dependencies safely.
"""

import subprocess
import sys
import os
import time

def kill_pip_processes():
    """Kill any stuck pip processes"""
    print("🔧 Killing stuck pip processes...")
    try:
        subprocess.run("taskkill /f /im pip.exe", shell=True, capture_output=True)
        subprocess.run("taskkill /f /im python.exe", shell=True, capture_output=True)
        time.sleep(2)
        print("✅ Processes cleared")
    except:
        print("⚠️ Could not kill processes (might not exist)")

def safe_pip_install(package, description, max_retries=3):
    """Safely install a package with retries"""
    for attempt in range(max_retries):
        print(f"\n🔧 {description} (Attempt {attempt + 1}/{max_retries})")
        try:
            # Use python -m pip to avoid exe locks
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", package
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print(f"✅ Success: {description}")
                return True
            else:
                print(f"❌ Failed: {description}")
                if result.stderr:
                    print(f"Error: {result.stderr.strip()}")
                
                if attempt < max_retries - 1:
                    print("⏳ Waiting before retry...")
                    time.sleep(5)
                    kill_pip_processes()
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Timeout during {description}")
            kill_pip_processes()
        except Exception as e:
            print(f"❌ Exception during {description}: {e}")
    
    return False

def check_import(module_name, display_name):
    """Check if a module can be imported"""
    try:
        __import__(module_name)
        print(f"✅ {display_name}: OK")
        return True
    except ImportError:
        print(f"❌ {display_name}: FAILED")
        return False

def main():
    print("🚀 Safe Installation Script for InsureMyWay")
    print("=" * 60)
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
    else:
        print("⚠️ WARNING: Not in a virtual environment!")
    
    # Kill any stuck processes first
    kill_pip_processes()
    
    # Clear pip cache
    print("\n🧹 Clearing pip cache...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "cache", "purge"], 
                      capture_output=True, timeout=60)
        print("✅ Cache cleared")
    except:
        print("⚠️ Could not clear cache")
    
    print("\n" + "=" * 60)
    print("📦 Installing Core Dependencies")
    print("=" * 60)
    
    # Core dependencies in order
    core_deps = [
        ("Flask==2.3.2", "Flask web framework"),
        ("Werkzeug==2.3.6", "WSGI utility library"),
        ("Flask-SQLAlchemy==3.0.5", "Flask SQLAlchemy extension"),
        ("Flask-Bcrypt==1.0.1", "Flask Bcrypt extension"),
        ("Flask-Login==0.6.2", "Flask Login extension"),
        ("Flask-WTF==1.1.1", "Flask WTF forms extension"),
    ]
    
    failed_core = []
    for package, description in core_deps:
        if not safe_pip_install(package, description):
            failed_core.append(package)
    
    if failed_core:
        print(f"\n❌ Failed to install core dependencies: {failed_core}")
        print("The app will not work without these. Please try manual installation:")
        for package in failed_core:
            print(f"  python -m pip install {package}")
        return False
    
    print("\n" + "=" * 60)
    print("🤖 Installing ML Dependencies")
    print("=" * 60)
    
    # ML dependencies
    ml_deps = [
        ("numpy==1.24.3", "NumPy numerical computing"),
        ("pandas==2.0.3", "Pandas data analysis"),
        ("scikit-learn==1.3.0", "Scikit-learn machine learning"),
        ("scipy==1.11.1", "SciPy scientific computing"),
        ("joblib==1.3.1", "Joblib parallel computing"),
    ]
    
    for package, description in ml_deps:
        safe_pip_install(package, description)
    
    print("\n" + "=" * 60)
    print("📄 Installing PDF Dependencies (Optional)")
    print("=" * 60)
    
    # PDF dependencies
    pdf_deps = [
        ("Pillow", "PIL image processing"),
        ("reportlab", "ReportLab PDF generation"),
    ]
    
    for package, description in pdf_deps:
        safe_pip_install(package, description)
    
    print("\n" + "=" * 60)
    print("✅ Verification")
    print("=" * 60)
    
    # Test core imports
    core_working = True
    core_working &= check_import('flask', 'Flask')
    core_working &= check_import('flask_sqlalchemy', 'Flask-SQLAlchemy')
    core_working &= check_import('flask_bcrypt', 'Flask-Bcrypt')
    
    # Test optional imports
    check_import('sklearn', 'Scikit-learn')
    check_import('pandas', 'Pandas')
    check_import('numpy', 'NumPy')
    check_import('PIL', 'PIL/Pillow')
    check_import('reportlab', 'ReportLab')
    
    print("\n" + "=" * 60)
    if core_working:
        print("🎉 SUCCESS! Core dependencies are working!")
        print("✅ You can now run: python app.py")
        
        # Try to start the app
        print("\n🚀 Attempting to start the application...")
        try:
            import app
            print("✅ App imported successfully!")
        except Exception as e:
            print(f"⚠️ App import failed: {e}")
            print("But you can still try: python app.py")
    else:
        print("❌ Core dependencies failed. Please install manually.")
    
    return core_working

if __name__ == "__main__":
    main()
