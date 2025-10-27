"""
Script to list all available guardrails in your AWS account
"""
import boto3
import os
from dotenv import load_dotenv

load_dotenv()

print("=" * 70)
print("AWS BEDROCK GUARDRAILS DISCOVERY")
print("=" * 70)

# Get AWS configuration
region = os.getenv('AWS_REGION', 'us-east-1')
aws_key = os.getenv('AWS_ACCESS_KEY_ID')
aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY')

print(f"\nAWS Region: {region}")
print(f"Using AWS Credentials: {'Yes (from env)' if aws_key else 'Yes (from IAM role/default)'}")

# Initialize Bedrock client
try:
    aws_kwargs = {
        'service_name': 'bedrock',
        'region_name': region
    }
    
    if aws_key and aws_secret:
        aws_kwargs['aws_access_key_id'] = aws_key
        aws_kwargs['aws_secret_access_key'] = aws_secret
    
    client = boto3.client(**aws_kwargs)
    print("✓ Successfully connected to AWS Bedrock")
    
except Exception as e:
    print(f"✗ Failed to connect to AWS Bedrock: {e}")
    print("\nPlease check:")
    print("1. AWS credentials are configured")
    print("2. You have permissions for bedrock:ListGuardrails")
    print("3. The region is correct")
    exit(1)

print("\n" + "=" * 70)
print("LISTING ALL GUARDRAILS")
print("=" * 70)

try:
    # List all guardrails
    response = client.list_guardrails(maxResults=50)
    
    guardrails = response.get('guardrails', [])
    
    if not guardrails:
        print("\n⚠ No guardrails found in this region!")
        print("\nPossible reasons:")
        print("1. No guardrails created yet in this account/region")
        print("2. Wrong region - check AWS Console to see which region has guardrails")
        print("3. Insufficient permissions to list guardrails")
        print("\nTo create a guardrail:")
        print("- Go to AWS Console → Bedrock → Guardrails")
        print("- Click 'Create guardrail'")
    else:
        print(f"\n✓ Found {len(guardrails)} guardrail(s):\n")
        
        for i, gr in enumerate(guardrails, 1):
            print(f"{i}. Guardrail: {gr['name']}")
            print(f"   ID: {gr['id']}")
            print(f"   Status: {gr['status']}")
            print(f"   Created: {gr.get('createdAt', 'N/A')}")
            print(f"   Updated: {gr.get('updatedAt', 'N/A')}")
            
            # Get detailed guardrail info to see versions
            try:
                detail_response = client.get_guardrail(
                    guardrailIdentifier=gr['id'],
                    guardrailVersion='DRAFT'
                )
                
                print(f"   Available Versions:")
                print(f"     - DRAFT (current working version)")
                
                # Try to get the numbered version if it exists
                try:
                    version_response = client.get_guardrail(
                        guardrailIdentifier=gr['id'],
                        guardrailVersion='1'
                    )
                    print(f"     - Version 1")
                except:
                    pass
                
            except Exception as e:
                if 'ResourceNotFoundException' not in str(e):
                    print(f"   ⚠ Could not get guardrail details: {e}")
            
            print(f"   \n   🔧 Use in .env file:")
            print(f"      GUARDRAILS_IDS={gr['id']}:DRAFT")
            print(f"      or")
            print(f"      GUARDRAILS_IDS={gr['id']}:1")
            print()
        
        print("=" * 70)
        print("RECOMMENDED .ENV CONFIGURATION")
        print("=" * 70)
        print("\nCopy one of these lines to your .env file:\n")
        
        for gr in guardrails[:3]:  # Show first 3
            print(f"# For '{gr['name']}':")
            print(f"GUARDRAILS_IDS={gr['id']}:DRAFT")
            print()

except Exception as e:
    print(f"\n✗ Error listing guardrails: {e}")
    print(f"\nError type: {type(e).__name__}")
    
    if 'AccessDenied' in str(e):
        print("\n🔒 PERMISSION ISSUE")
        print("You need the following IAM permissions:")
        print("  - bedrock:ListGuardrails")
        print("  - bedrock:GetGuardrail")
        print("  - bedrock:ApplyGuardrail")
    
    elif 'InvalidRegion' in str(e):
        print("\n🌍 REGION ISSUE")
        print("Bedrock Guardrails might not be available in this region.")
        print("Try these regions: us-east-1, us-west-2, eu-west-1")
    
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("\n1. If you see guardrails listed above:")
print("   - Copy the GUARDRAILS_IDS line to your .env file")
print("   - Run: python test_guardrails.py")
print("\n2. If no guardrails found:")
print("   - Create one in AWS Console → Bedrock → Guardrails")
print("   - Or check if you're looking in the correct region")
print("\n3. If you get permission errors:")
print("   - Contact your AWS administrator")
print("   - Request bedrock:ListGuardrails permission")
