#!/usr/bin/env python3
"""
Lambda Layer作成スクリプト（最小限のモジュール）
"""
import os
import subprocess
import boto3
import zipfile
import shutil
from pathlib import Path

def create_layer_package():
    """Lambda Layer用のパッケージを作成"""
    print("Lambda Layer用パッケージを作成中...")
    
    # 一時ディレクトリ作成
    temp_dir = Path("lambda_layer_temp")
    python_dir = temp_dir / "python"
    python_dir.mkdir(parents=True, exist_ok=True)
    
    # 必要最小限のモジュールをインストール
    essential_modules = [
        "yfinance",
        "requests",
        "anthropic",
        "notion-client",
        "tweepy"
    ]
    
    print("必要なモジュールをインストール中...")
    for module in essential_modules:
        print(f"  - {module}")
    
    subprocess.run([
        "pip3", "install", 
        "--platform", "manylinux_2_17_x86_64", 
        "--target", str(python_dir),
        "--only-binary", ":all:",
        "--upgrade"
    ] + essential_modules, check=True)
    
    # ZIPファイル作成
    zip_path = "fx_minimal_layer.zip"
    print(f"\nZIPファイルを作成中: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            # 不要なファイルを除外
            dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
            
            for file in files:
                if not file.endswith(('.pyc', '.pyo', '.dist-info')):
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(temp_dir)
                    zipf.write(file_path, arcname)
    
    # 一時ディレクトリを削除
    shutil.rmtree(temp_dir)
    
    # ファイルサイズを確認
    size_mb = os.path.getsize(zip_path) / (1024 * 1024)
    print(f"✅ Lambda Layerパッケージ作成完了: {zip_path} ({size_mb:.1f} MB)")
    
    return zip_path

def publish_layer(region="ap-northeast-1"):
    """Lambda Layerを公開"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        # Layerパッケージを作成
        zip_path = create_layer_package()
        
        # ZIPファイルを読み込み
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
        
        print("\nLambda Layerを公開中...")
        
        # Layer公開
        response = lambda_client.publish_layer_version(
            LayerName='fx-analyzer-minimal',
            Description='Minimal dependencies for FX Analyzer',
            Content={'ZipFile': zip_data},
            CompatibleRuntimes=['python3.8', 'python3.9', 'python3.10', 'python3.11', 'python3.12', 'python3.13']
        )
        
        layer_arn = response['LayerVersionArn']
        print(f"✅ Lambda Layer公開完了")
        print(f"   Layer ARN: {layer_arn}")
        
        # クリーンアップ
        os.remove(zip_path)
        
        return layer_arn
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        return None

def update_function_layers(layer_arn, function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数のLayerを更新"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        print(f"\nLambda関数 '{function_name}' のLayerを更新中...")
        
        # 既存のpytz-layerと新しいLayerを両方設定
        pytz_layer = "arn:aws:lambda:ap-northeast-1:455931011903:layer:pytz-layer:1"
        
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Layers=[pytz_layer, layer_arn]
        )
        
        print("✅ Layer更新完了")
        print(f"   現在のLayers: {len(response.get('Layers', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Layer更新エラー: {e}")
        return False

def main():
    print("=== Lambda Layer作成・更新スクリプト（最小限版） ===\n")
    
    # AWS認証情報の確認
    try:
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        print(f"AWS Account: {identity['Account']}")
        print(f"User ARN: {identity['Arn']}\n")
    except Exception as e:
        print(f"❌ AWS認証エラー: {e}")
        return
    
    # Lambda Layerを公開
    layer_arn = publish_layer()
    
    if layer_arn:
        # Lambda関数のLayerを更新
        if update_function_layers(layer_arn):
            print("\n✅ 完了！")
            print("必要なモジュールがLambda関数で使用できるようになりました。")
        else:
            print("\n⚠️  Layer作成は成功しましたが、関数への追加に失敗しました。")
            print(f"手動で以下のLayer ARNを追加してください:")
            print(f"{layer_arn}")
    else:
        print("\n❌ Layer作成に失敗しました")

if __name__ == "__main__":
    main()