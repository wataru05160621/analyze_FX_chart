#!/usr/bin/env python3
"""
ECS Fargate用のヘルスチェックスクリプト
"""
import sys
import os
import logging

def health_check():
    """基本的なヘルスチェック"""
    try:
        # 基本的なインポートテスト
        import yfinance
        import matplotlib
        import mplfinance
        import anthropic
        import notion_client
        
        # 必要なディレクトリの確認
        required_dirs = ['/app/screenshots', '/app/logs']
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                print(f"ERROR: Required directory missing: {dir_path}")
                return False
        
        # 環境変数の確認（本番環境では実際のチェックを行う）
        if os.getenv('ECS_HEALTH_CHECK') == 'full':
            required_env_vars = [
                'CLAUDE_API_KEY',
                'NOTION_API_KEY', 
                'NOTION_DATABASE_ID'
            ]
            
            for var in required_env_vars:
                if not os.getenv(var):
                    print(f"ERROR: Missing environment variable: {var}")
                    return False
        
        print("Health check passed")
        return True
        
    except ImportError as e:
        print(f"ERROR: Import failed: {e}")
        return False
    except Exception as e:
        print(f"ERROR: Health check failed: {e}")
        return False

if __name__ == "__main__":
    if health_check():
        sys.exit(0)
    else:
        sys.exit(1)