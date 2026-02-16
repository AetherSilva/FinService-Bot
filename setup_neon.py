#!/usr/bin/env python3
"""
Neon Database Setup Assistant
Interactive script to configure PostgreSQL connection
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def print_header(text):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60 + "\n")

def print_section(text):
    """Print a section header"""
    print(f"\n📌 {text}\n")

def test_postgres_connection(connection_string):
    """Test PostgreSQL connection"""
    try:
        import psycopg2
        con = psycopg2.connect(connection_string)
        cur = con.cursor()
        cur.execute("SELECT version()")
        version = cur.fetchone()[0]
        con.close()
        return True, version
    except ImportError:
        return False, "psycopg2 not installed"
    except Exception as e:
        return False, str(e)

def check_env_file():
    """Check if .env file exists"""
    env_path = Path(".env")
    if env_path.exists():
        print(f"✅ Found .env file at {env_path}")
        return True
    else:
        print(f"❌ No .env file found at {env_path}")
        return False

def create_env_file():
    """Create a new .env file with DATABASE_URL"""
    print_section("Create .env File")
    
    # Check if .env already exists
    env_path = Path(".env")
    if env_path.exists():
        response = input("❓ .env file already exists. Overwrite? (y/n): ").strip().lower()
        if response != 'y':
            print("⏭ Skipping .env creation")
            return False
    
    print("""
📝 Add your credentials to .env file.

You'll need:
1. TELEGRAM_BOT_TOKEN - From BotFather
2. ADMIN_IDS - Your Telegram user IDs
3. DATABASE_URL - From Neon console

Example format:
    postgresql://username:password@host/neondb
    """)
    
    entries = {}
    
    # Get DATABASE_URL
    print("\n🔗 Neon Database URL:")
    db_url = input("Enter DATABASE_URL (or 'skip' to use SQLite): ").strip()
    if db_url.lower() != 'skip' and db_url:
        entries["DATABASE_URL"] = db_url
    
    # Get TELEGRAM_BOT_TOKEN
    print("\n🤖 Telegram Bot Configuration:")
    bot_token = input("Enter TELEGRAM_BOT_TOKEN: ").strip()
    if bot_token:
        entries["TELEGRAM_BOT_TOKEN"] = bot_token
    
    # Get ADMIN_IDS
    admin_ids = input("Enter ADMIN_IDS (comma-separated): ").strip()
    if admin_ids:
        entries["ADMIN_IDS"] = admin_ids
    
    # Get SESSION_SECRET
    session_secret = input("Enter SESSION_SECRET (any string): ").strip()
    if session_secret:
        entries["SESSION_SECRET"] = session_secret
    
    # Write to .env
    if entries:
        with open(".env", "w") as f:
            for key, value in entries.items():
                f.write(f"{key}={value}\n")
        
        print(f"\n✅ Created .env with {len(entries)} entries")
        return True
    else:
        print("\n⚠️ No entries to save")
        return False

def verify_database():
    """Verify database configuration"""
    print_section("Verify Database Configuration")
    
    load_dotenv()
    
    db_url = os.getenv("DATABASE_URL")
    
    if db_url:
        print(f"📦 DATABASE_URL detected: {db_url[:50]}...")
        print("🧪 Testing connection...")
        
        success, result = test_postgres_connection(db_url)
        
        if success:
            print(f"✅ Connection successful!")
            print(f"📊 Server version: {result[:80]}...")
            return "postgresql"
        else:
            print(f"❌ Connection failed: {result}")
            print("⚠️  Will use SQLite fallback")
            return "sqlite_fallback"
    else:
        print("📂 No DATABASE_URL found")
        print("✅ Using SQLite default")
        return "sqlite"

def run_tests():
    """Run database tests"""
    print_section("Run Database Tests")
    
    print("🧪 Running test_db_universal.py...\n")
    
    import subprocess
    result = subprocess.run([sys.executable, "test_db_universal.py"], capture_output=False)
    
    return result.returncode == 0

def show_neon_instructions():
    """Show Neon setup instructions"""
    print_section("Get Neon Database Connection String")
    
    instructions = """
📚 Follow these steps to get your connection string:

1. Go to https://console.neon.tech/auth/signup
2. Sign up with email or GitHub
3. Create a new project (default settings OK)
4. In the dashboard, select your project
5. Click 'Databases' → 'neondb'
6. Click 'Connection details' (top right)
7. Copy the connection string under "Direct connection"

⚠️ The connection string will look like:
   postgresql://username:password@your-neon-host/neondb

🔐 Keep this private - don't share with anyone!

After copying, paste it when prompted in this setup wizard.
    """
    
    print(instructions)
    
    input("Press Enter to continue...")

def main():
    """Main setup wizard"""
    print_header("🚀 FinService-Bot Neon Setup Wizard")
    
    print("""
This interactive setup will help you configure PostgreSQL via Neon.

Features:
  ✅ Test database connection
  ✅ Create .env file
  ✅ Run verification tests
  ✅ Show deployment instructions
    """)
    
    while True:
        print("\n" + "=" * 60)
        print("📋 Setup Menu")
        print("=" * 60)
        print("""
1. 📌 Show Neon Instructions (get connection string)
2. 🔧 Setup .env File (add DATABASE_URL)
3. ✅ Verify Database Configuration
4. 🧪 Run Database Tests
5. 📚 View Deployment Options
6. 🚀 Test Everything & Show Summary
7. ❌ Exit
        """)
        
        choice = input("Select option (1-7): ").strip()
        
        if choice == "1":
            show_neon_instructions()
        
        elif choice == "2":
            create_env_file()
        
        elif choice == "3":
            db_type = verify_database()
            print(f"\n🎯 Database type: {db_type.upper()}")
        
        elif choice == "4":
            success = run_tests()
            if success:
                print("\n✅ All tests passed!")
            else:
                print("\n❌ Some tests failed")
        
        elif choice == "5":
            print_section("📚 Deployment Options")
            print("""
After Neon setup, deploy to:

🔴 RENDER.COM
   - Update render.yaml with DATABASE_URL
   - Push to GitHub
   - Deploy from Render dashboard
   
🟣 HEROKU
   - heroku create your-app
   - heroku config:set DATABASE_URL="..."
   - git push heroku main

🏠 REPLIT
   - Set DATABASE_URL in Secrets
   - Run: python main.py

📖 See NEON_SETUP.md for detailed instructions
            """)
        
        elif choice == "6":
            print_header("🧪 Running Full Verification")
            
            # Check environment
            print("\n📋 Checking prerequisites...")
            if check_env_file():
                load_dotenv()
            
            # Test database
            print("\n🔌 Testing database...")
            db_type = verify_database()
            
            # Run tests
            print("\n🧪 Running tests...")
            if run_tests():
                print_header("✅ Setup Complete!")
                print("""
Your FinService-Bot is ready to use!

📊 Configuration Summary:
   - Database: """ + db_type.upper() + """
   - Environment: Configured
   - Tests: All passing
   - Status: Ready for deployment

🚀 Next Steps:
   1. Run: python main.py (local testing)
   2. Deploy to Render/Heroku/Replit
   3. Monitor via Neon dashboard
   4. Enjoy! 🎉
                """)
            else:
                print("\n⚠️  Some tests failed - check configuration")
        
        elif choice == "7":
            print("\n👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid option. Please try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
