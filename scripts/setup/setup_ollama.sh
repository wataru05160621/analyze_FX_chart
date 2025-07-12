#!/bin/bash
# Ollama セットアップスクリプト

echo "=== Ollama セットアップ ==="
echo

# Ollamaのインストール確認
if ! command -v ollama &> /dev/null; then
    echo "Ollamaをインストールします..."
    brew install ollama
else
    echo "✅ Ollamaは既にインストールされています"
fi

# Ollamaサービスの起動
echo
echo "Ollamaサービスを起動します..."
ollama serve &
OLLAMA_PID=$!
sleep 5

# LLaVAモデルのダウンロード
echo
echo "LLaVAモデルをダウンロードします（約4.7GB）..."
ollama pull llava

# その他の推奨モデル
echo
echo "その他の推奨モデル（オプション）:"
echo "1. bakllava (より高性能、約4.7GB): ollama pull bakllava"
echo "2. llava:13b (より高精度、約8GB): ollama pull llava:13b"

echo
echo "✅ セットアップ完了!"
echo
echo "使用方法:"
echo "1. python3 execute_with_ollama.py"
echo
echo "Ollamaサービスを停止するには:"
echo "kill $OLLAMA_PID"