#!/usr/bin/env python3
"""
Dependency Installation Script for InsureMyWay Web Application
This script installs all required dependencies in the correct order.
"""

import subprocess
import sys
import os

def run_pip_command(command, description):
    """Run a pip command and return success status"""
    print(f"\n🔧 {description}")
    print(f"Running: {command}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Success: {description}")
            return True
        else:
            print(f"❌ Failed: {description}")
            if result.stderr:
                print(f"Error: {result.stderr.strip()}")
            return False
    except Exception as e:
        print(f"❌ Exception during {description}: {e}")
        return False

def check_virtual_env():
    """Check if we're in a virtual environment"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️ WARNING: Not in a virtual environment!")
        print("Please activate your virtual environment first:")
        print("  venv\\Scripts\\activate")
        return False

def main():
    print("🚀 InsureMyWay Dependency Installation Script")
    print("=" * 60)
    
    # Check virtual environment
    if not check_virtual_env():
        input("Press Enter to continue anyway, or Ctrl+C to exit...")
    
    print(f"\n🐍 Python Version: {sys.version}")
    print(f"📁 Current Directory: {os.getcwd()}")
    
    # Core dependencies that must be installed first
    core_dependencies = [
        ("pip install --upgrade pip", "Upgrading pip"),
        ("pip install Flask==2.3.2", "Installing Flask"),
        ("pip install Flask-SQLAlchemy==3.0.5", "Installing Flask-SQLAlchemy"),
        ("pip install Flask-Bcrypt==1.0.1", "Installing Flask-Bcrypt"),
        ("pip install Werkzeug==2.3.6", "Installing Werkzeug"),
        ("pip install Flask-Login==0.6.2", "Installing Flask-Login"),
        ("pip install Flask-WTF==1.1.1", "Installing Flask-WTF"),
    ]
    
    # ML dependencies
    ml_dependencies = [
        ("pip install numpy==1.24.3", "Installing NumPy"),
        ("pip install pandas==2.0.3", "Installing Pandas"),
        ("pip install scikit-learn==1.3.0", "Installing Scikit-learn"),
        ("pip install scipy==1.11.1", "Installing SciPy"),
        ("pip install joblib==1.3.1", "Installing Joblib"),
    ]
    
    # Optional PDF dependencies
    pdf_dependencies = [
        ("pip install Pillow", "Installing Pillow (for PDF generation)"),
        ("pip install reportlab", "Installing ReportLab (for PDF generation)"),
    ]
    
    print("\n" + "=" * 60)
    print("📦 STEP 1: Installing Core Dependencies")
    print("=" * 60)
    
    core_success = True
    for command, description in core_dependencies:
        if not run_pip_command(command, description):
            core_success = False
    
    if not core_success:
        print("\n❌ Some core dependencies failed to install!")
        print("Try running manually:")
        for command, _ in core_dependencies:
            print(f"  {command}")
        return False
    
    print("\n" + "=" * 60)
    print("🤖 STEP 2: Installing ML Dependencies")
    print("=" * 60)
    
    for command, description in ml_dependencies:
        run_pip_command(command, description)
    
    print("\n" + "=" * 60)
    print("📄 STEP 3: Installing PDF Dependencies (Optional)")
    print("=" * 60)
    
    pdf_success = True
    for command, description in pdf_dependencies:
        if not run_pip_command(command, description):
            pdf_success = False
    
    if not pdf_success:
        print("\n⚠️ PDF dependencies failed - but that's OK!")
        print("The app will work without PDF generation features.")
    
    print("\n" + "=" * 60)
    print("✅ STEP 4: Verification")
    print("=" * 60)
    
    # Test imports
    test_imports = [
        ('flask', 'Flask'),
        ('flask_sqlalchemy', 'Flask-SQLAlchemy'),
        ('flask_bcrypt', 'Flask-Bcrypt'),
        ('sklearn', 'Scikit-learn'),
        ('pandas', 'Pandas'),
        ('numpy', 'NumPy'),
    ]
    
    all_working = True
    for module, name in test_imports:
        try:
            __import__(module)
            print(f"✅ {name}: OK")
        except ImportError:
            print(f"❌ {name}: FAILED")
            all_working = False
    
    # Test optional imports
    try:
        from PIL import Image
        print("✅ PIL/Pillow: OK")
    except ImportError:
        print("⚠️ PIL/Pillow: Not available (PDF generation disabled)")
    
    try:
        from reportlab.pdfgen import canvas
        print("✅ ReportLab: OK")
    except ImportError:
        print("⚠️ ReportLab: Not available (PDF generation disabled)")
    
    print("\n" + "=" * 60)
    if all_working:
        print("🎉 SUCCESS! All core dependencies installed successfully!")
        print("✅ You can now run: python app.py")
    else:
        print("⚠️ Some dependencies failed, but the app might still work.")
        print("Try running: python app.py")
    
    print("\n📋 Next Steps:")
    print("1. Run: python app.py")
    print("2. Open browser: http://127.0.0.1:5000")
    print("3. If issues persist, check the error messages above")
    
    return all_working

if __name__ == "__main__":
    main()
