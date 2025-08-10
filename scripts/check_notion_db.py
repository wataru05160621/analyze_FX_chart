#!/usr/bin/env python
"""Check Notion database properties and status options."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from notion_client import Client
from src.utils.config import config
import json

def check_notion_database():
    """Check Notion database configuration."""
    
    print("🔍 Checking Notion Database Configuration")
    print("=" * 60)
    
    if not config.notion_api_key or not config.notion_db_id:
        print("❌ Notion API key or database ID not configured")
        return
    
    try:
        client = Client(auth=config.notion_api_key)
        
        # Get database schema
        db = client.databases.retrieve(database_id=config.notion_db_id)
        
        print(f"📊 Database Title: {db.get('title', [{}])[0].get('plain_text', 'N/A')}")
        print(f"🆔 Database ID: {config.notion_db_id}")
        print("\n📋 Properties:")
        
        for prop_name, prop_config in db['properties'].items():
            prop_type = prop_config['type']
            print(f"\n  • {prop_name} ({prop_type})")
            
            # Show status options if it's a status property
            if prop_type == 'status':
                if 'status' in prop_config and 'options' in prop_config['status']:
                    print("    Available options:")
                    for option in prop_config['status']['options']:
                        print(f"      - {option['name']} (color: {option.get('color', 'default')})")
                    
                    # Show groups if available
                    if 'groups' in prop_config['status']:
                        print("    Groups:")
                        for group in prop_config['status']['groups']:
                            print(f"      - {group['name']}: {', '.join(group.get('option_ids', []))}")
            
            # Show select options
            elif prop_type == 'select':
                if 'select' in prop_config and 'options' in prop_config['select']:
                    print("    Available options:")
                    for option in prop_config['select']['options']:
                        print(f"      - {option['name']}")
            
            # Show multi-select options
            elif prop_type == 'multi_select':
                if 'multi_select' in prop_config and 'options' in prop_config['multi_select']:
                    print("    Available options:")
                    for option in prop_config['multi_select']['options']:
                        print(f"      - {option['name']}")
        
        print("\n" + "=" * 60)
        print("✅ Database check completed")
        
        # Save to file for reference
        with open('notion_db_schema.json', 'w') as f:
            json.dump(db, f, indent=2, default=str)
        print("📄 Full schema saved to notion_db_schema.json")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_notion_database()