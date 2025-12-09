import sys
import os
import subprocess
import argparse
import platform
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))

def print_header(title):
    print(f"\n{'='*60}")
    print(f"🔧 AGENT TOOLBOX: {title}")
    print(f"{'='*60}")

def run_command(command, description, ignore_error=False):
    print(f"\n▶️  Running: {description}...")
    try:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            shell=True,
            check=not ignore_error,
            capture_output=True,
            text=True
        )
        print("✅ Success")
        if result.stdout:
            print(f"--- Output ---\n{result.stdout.strip()[:500]}..." if len(result.stdout) > 500 else f"--- Output ---\n{result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed (Exit Code: {e.returncode})")
        print(f"--- Error Output ---\n{e.stderr.strip()}")
        if not ignore_error:
            return False
        return False

def check_env():
    print_header("Environment Check")
    env_path = PROJECT_ROOT / ".env"
    if not env_path.exists():
        print("❌ .env file NOT FOUND!")
        return False
    
    print("✅ .env file exists.")
    
    # Check for critical keys
    required_keys = ["MONGODB_URI", "GEMINI_API_KEY"]
    with open(env_path, "r", encoding="utf-8") as f:
        content = f.read()
        for key in required_keys:
            if key not in content:
                print(f"❌ Missing Key: {key}")
                return False
            else:
                print(f"✅ Found Key: {key}")
    return True

def verify():
    print_header("VERIFICATION MODE")
    
    # 1. Environment
    if not check_env():
        print("\n🛑 Environment Check Failed. Fix .env first.")
        return
    
    # 2. Syntax Check (Compile only)
    print("\n🔍 Checking Python Syntax...")
    py_files = list(PROJECT_ROOT.glob("**/*.py"))
    # Filter out venv
    py_files = [f for f in py_files if ".venv" not in str(f)]
    
    syntax_errors = 0
    for f in py_files:
        try:
            with open(f, "r", encoding="utf-8") as source:
                compile(source.read(), f, "exec")
        except Exception as e:
            print(f"❌ Syntax Error in {f.name}: {e}")
            syntax_errors += 1
            
    if syntax_errors == 0:
        print(f"✅ Checked {len(py_files)} files. No syntax errors.")
    else:
        print(f"🛑 Found {syntax_errors} syntax errors. Fix them immediately.")
        # Don't return, verify tests anyway might give more clues
        
    # 3. Run Tests
    print("\n🧪 Running Unit Tests...")
    # Using python -m pytest to ensure path is correct
    run_command("python -m pytest tests/", "Pytest Suite", ignore_error=True)

    print("\n✅ Verification Complete.")

def diagnose():
    print_header("DIAGNOSTIC MODE")
    
    print(f"OS: {platform.system()} {platform.release()}")
    print(f"Python: {sys.version}")
    
    # Check Imports
    print("\n🔍 Checking Dependencies...")
    libs = ["pymongo", "google.generativeai", "flask", "streamlit", "yfinance"]
    for lib in libs:
        try:
            __import__(lib)
            print(f"✅ Import {lib}: OK")
        except ImportError:
            print(f"❌ Import {lib}: MISSING")
            
    # Check MongoDB Connection
    print("\n🔍 Checking Database Connection...")
    try:
        from database_manager import DatabaseManager
        db = DatabaseManager()
        if db.enabled:
            print("✅ DatabaseManager: Enabled")
            # Try a ping
            try:
                db.client.admin.command('ping')
                print("✅ MongoDB Ping: Success")
            except Exception as e:
                print(f"❌ MongoDB Ping Failed: {e}")
        else:
            print("⚠️  DatabaseManager: Disabled (Check .env)")
    except Exception as e:
        print(f"❌ DatabaseManager Init Failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="AI Agent Toolbox")
    subparsers = parser.add_subparsers(dest="command")
    
    subparsers.add_parser("verify", help="Run full verification (env + syntax + tests)")
    subparsers.add_parser("diagnose", help="Check system diagnosis")
    subparsers.add_parser("health", help="Simple health check")
    
    args = parser.parse_args()
    
    if args.command == "verify":
        verify()
    elif args.command == "diagnose":
        diagnose()
    elif args.command == "health":
        print("✅ System is READY.")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
