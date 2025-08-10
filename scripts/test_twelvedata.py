#!/usr/bin/env python
"""Test TwelveData API key validity."""

import sys
import requests
import boto3
import json

def get_api_key_from_secrets():
    """Get API key from AWS Secrets Manager."""
    client = boto3.client('secretsmanager', region_name='ap-northeast-1')
    try:
        response = client.get_secret_value(SecretId='TWELVEDATA_API_KEY')
        return response['SecretString']
    except Exception as e:
        print(f"❌ Failed to get API key from Secrets Manager: {e}")
        return None

def test_api_key(api_key):
    """Test if API key is valid by making a simple API call."""
    url = "https://api.twelvedata.com/quote"
    params = {
        "symbol": "USD/JPY",
        "apikey": api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if response.status_code == 200 and "symbol" in data:
            print("✅ API key is valid!")
            print(f"   Symbol: {data.get('symbol')}")
            print(f"   Price: {data.get('close')}")
            print(f"   Exchange: {data.get('exchange')}")
            return True
        elif "message" in data:
            print(f"❌ API error: {data['message']}")
            return False
        else:
            print(f"❌ Unexpected response: {data}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def main():
    """Main function."""
    print("🔍 Testing TwelveData API key from AWS Secrets Manager...")
    
    # Get API key
    api_key = get_api_key_from_secrets()
    if not api_key:
        sys.exit(1)
    
    # Mask the key for display
    masked_key = api_key[:10] + "..." + api_key[-4:] if len(api_key) > 14 else "***"
    print(f"   API key: {masked_key}")
    print(f"   Length: {len(api_key)} characters")
    
    # Test the key
    print("\n📡 Testing API connection...")
    if test_api_key(api_key):
        print("\n✅ TwelveData API key is configured correctly!")
        sys.exit(0)
    else:
        print("\n❌ API key validation failed. Please check your key.")
        sys.exit(1)

if __name__ == "__main__":
    main()