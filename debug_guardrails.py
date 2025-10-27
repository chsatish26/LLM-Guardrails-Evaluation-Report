"""
Debug script to check guardrails configuration
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=" * 70)
print("GUARDRAILS CONFIGURATION DEBUG")
print("=" * 70)

# Check if .env file exists
if os.path.exists('.env'):
    print("✓ .env file found")
    print("\nReading .env file content:")
    with open('.env', 'r') as f:
        for line in f:
            if 'GUARDRAIL' in line:
                print(f"  {line.strip()}")
else:
    print("✗ .env file NOT found in current directory")
    print(f"  Current directory: {os.getcwd()}")

print("\n" + "=" * 70)
print("ENVIRONMENT VARIABLES")
print("=" * 70)

# Check environment variables
guardrails_enabled = os.getenv('GUARDRAILS_ENABLED')
guardrails_ids = os.getenv('GUARDRAILS_IDS')
guardrails_mode = os.getenv('GUARDRAILS_MODE')

print(f"GUARDRAILS_ENABLED: {guardrails_enabled}")
print(f"GUARDRAILS_IDS: {guardrails_ids}")
print(f"GUARDRAILS_MODE: {guardrails_mode}")

print("\n" + "=" * 70)
print("PARSING GUARDRAILS_IDS")
print("=" * 70)

if guardrails_ids:
    print(f"Raw value: '{guardrails_ids}'")
    print(f"Length: {len(guardrails_ids)}")
    
    guardrails = []
    for config in guardrails_ids.split(','):
        config = config.strip()
        print(f"\nProcessing: '{config}'")
        if ':' in config:
            guardrail_id, version = config.split(':', 1)
            guardrails.append({
                'id': guardrail_id.strip(),
                'version': version.strip()
            })
            print(f"  ID: {guardrail_id.strip()}")
            print(f"  Version: {version.strip()}")
        else:
            print(f"  ✗ No ':' separator found")
    
    print(f"\nTotal guardrails parsed: {len(guardrails)}")
    for i, gr in enumerate(guardrails, 1):
        print(f"  {i}. {gr['id']} (v{gr['version']})")
else:
    print("✗ GUARDRAILS_IDS is None or empty")

print("\n" + "=" * 70)
print("RECOMMENDATIONS")
print("=" * 70)

if not guardrails_ids:
    print("Issue: GUARDRAILS_IDS is not being read from .env file")
    print("\nPossible solutions:")
    print("1. Make sure .env file is in the same directory as your script")
    print("2. Check that GUARDRAILS_IDS line doesn't have extra spaces")
    print("3. Ensure the line is not commented out (no # at the start)")
    print("4. Try setting it as an environment variable:")
    print("   export GUARDRAILS_IDS='your-guardrail-id:1'")
    print("5. Check for hidden characters or encoding issues")

print("\n" + "=" * 70)