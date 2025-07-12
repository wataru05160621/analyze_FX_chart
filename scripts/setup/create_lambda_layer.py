#!/usr/bin/env python3
"""
Lambda Layer作成スクリプト（pytzモジュール用）
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
    
    # pytzをインストール
    print("pytzモジュールをインストール中...")
    subprocess.run([
        "pip3", "install", "pytz", "-t", str(python_dir)
    ], check=True)
    
    # ZIPファイル作成
    zip_path = "pytz_layer.zip"
    print(f"ZIPファイルを作成中: {zip_path}")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = file_path.relative_to(temp_dir)
                zipf.write(file_path, arcname)
    
    # 一時ディレクトリを削除
    shutil.rmtree(temp_dir)
    
    print(f"✅ Lambda Layerパッケージ作成完了: {zip_path}")
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
            LayerName='pytz-layer',
            Description='pytz module for Lambda',
            Content={'ZipFile': zip_data},
            CompatibleRuntimes=['python3.8', 'python3.9', 'python3.10', 'python3.11']
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

def attach_layer_to_function(layer_arn, function_name="fx-analyzer-prod", region="ap-northeast-1"):
    """Lambda関数にLayerを追加"""
    lambda_client = boto3.client('lambda', region_name=region)
    
    try:
        print(f"\nLambda関数 '{function_name}' にLayerを追加中...")
        
        # 現在の設定を取得
        config = lambda_client.get_function_configuration(FunctionName=function_name)
        current_layers = config.get('Layers', [])
        
        # Layer ARNのリストを作成
        layer_arns = [layer['Arn'] for layer in current_layers]
        if layer_arn not in layer_arns:
            layer_arns.append(layer_arn)
        
        # Lambda関数の設定を更新
        response = lambda_client.update_function_configuration(
            FunctionName=function_name,
            Layers=layer_arns
        )
        
        print("✅ Layer追加完了")
        print(f"   現在のLayers: {len(response.get('Layers', []))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Layer追加エラー: {e}")
        return False

def main():
    print("=== Lambda Layer作成・追加スクリプト ===\n")
    
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
        # Lambda関数にLayerを追加
        if attach_layer_to_function(layer_arn):
            print("\n✅ 完了！")
            print("pytzモジュールがLambda関数で使用できるようになりました。")
        else:
            print("\n⚠️  Layer作成は成功しましたが、関数への追加に失敗しました。")
            print(f"手動で以下のLayer ARNを追加してください:")
            print(f"{layer_arn}")
    else:
        print("\n❌ Layer作成に失敗しました")

if __name__ == "__main__":
    main()