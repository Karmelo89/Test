#!/usr/bin/env python3
"""
Solar Monitor Launcher
Automatically runs the appropriate version based on available dependencies.
"""

import sys
import subprocess
import importlib

def check_dependency(module_name):
    """Check if a module is available"""
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

def install_dependencies():
    """Try to install dependencies"""
    print("🔧 Attempting to install dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def run_full_version():
    """Run the full-featured Flask version"""
    print("🚀 Starting Full-Featured Solar Monitor...")
    print("   📊 Dashboard: http://localhost:5000")
    print("   ⚙️  Configuration: http://localhost:5000/config")
    print("   🤖 Machine Learning: Available")
    print("   🔌 Real Data Sources: Supported")
    print("")
    
    try:
        import app
        # The Flask app will run when imported
    except Exception as e:
        print(f"❌ Error running full version: {e}")
        print("🔄 Falling back to simple version...")
        run_simple_version()

def run_simple_version():
    """Run the simple HTTP server version"""
    print("🌞 Starting Simple Solar Monitor...")
    print("   📊 Dashboard: http://localhost:8000")
    print("   🔌 API: http://localhost:8000/api/current")
    print("   ✅ No external dependencies required")
    print("")
    
    try:
        import simple_app
        simple_app.main()
    except Exception as e:
        print(f"❌ Error running simple version: {e}")
        sys.exit(1)

def main():
    print("🌞 Solar Monitor System")
    print("=" * 50)
    
    # Check for required dependencies
    flask_available = check_dependency('flask')
    sklearn_available = check_dependency('sklearn')
    
    if flask_available and sklearn_available:
        print("✅ All dependencies available - Running full version")
        run_full_version()
    elif flask_available:
        print("⚠️  Some dependencies missing - Limited features available")
        choice = input("Run full version anyway? (y/N): ").lower()
        if choice == 'y':
            run_full_version()
        else:
            run_simple_version()
    else:
        print("⚠️  Flask not available - Running simple version")
        
        # Ask if user wants to try installing dependencies
        choice = input("Try to install dependencies? (y/N): ").lower()
        if choice == 'y':
            if install_dependencies():
                print("✅ Dependencies installed successfully!")
                # Try to run full version
                try:
                    flask_available = check_dependency('flask')
                    if flask_available:
                        run_full_version()
                        return
                except:
                    pass
            
        print("🔄 Using simple version with no external dependencies")
        run_simple_version()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Solar Monitor stopped by user")
        print("✅ Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Try running 'python3 simple_app.py' directly")
        sys.exit(1)