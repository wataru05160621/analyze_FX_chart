#!/bin/bash
# FX Chart Analyzer セットアップスクリプト

set -e  # エラー時に停止

echo "🚀 FX Chart Analyzer セットアップを開始します..."

# 色付きメッセージ用の関数
print_success() { echo -e "\033[32m✅ $1\033[0m"; }
print_error() { echo -e "\033[31m❌ $1\033[0m"; }
print_info() { echo -e "\033[34mℹ️ $1\033[0m"; }
print_warning() { echo -e "\033[33m⚠️ $1\033[0m"; }

# プロジェクトディレクトリに移動
cd "$(dirname "$0")"

# Python 3の確認
if ! command -v python3 &> /dev/null; then
    print_error "Python 3が見つかりません。Python 3をインストールしてください。"
    exit 1
fi

print_info "Python バージョン: $(python3 --version)"

# 仮想環境の作成
if [ ! -d "venv" ]; then
    print_info "仮想環境を作成中..."
    python3 -m venv venv
    print_success "仮想環境を作成しました"
else
    print_info "既存の仮想環境を使用します"
fi

# 仮想環境をアクティベート
source venv/bin/activate
print_success "仮想環境をアクティベートしました"

# pipをアップグレード
print_info "pipをアップグレード中..."
pip install --upgrade pip

# 依存関係をインストール
print_info "依存関係をインストール中..."
pip install -r requirements.txt

print_success "Pythonパッケージをインストールしました"

# Playwrightブラウザをインストール
print_info "Playwrightブラウザをインストール中..."
playwright install chromium
playwright install-deps

print_success "Playwrightブラウザをインストールしました"

# ディレクトリ作成
print_info "必要なディレクトリを作成中..."
mkdir -p logs screenshots

# .envファイルの確認
if [ ! -f ".env" ]; then
    print_warning ".envファイルが見つかりません"
    print_info ".env.exampleをコピーして.envを作成します"
    cp .env.example .env
    print_warning "⚠️ .envファイルを編集して必要な設定を行ってください！"
else
    print_success ".envファイルが存在します"
fi

# 権限設定
chmod +x scripts/*.sh scripts/*.py debug_tool.py run_scheduler.py

print_success "権限を設定しました"

# セットアップ完了
echo
echo "🎉 セットアップが完了しました！"
echo
echo "📋 次のステップ:"
echo "1. .envファイルを編集して必要な設定を行う"
echo "2. デバッグツールでシステムをテスト: python debug_tool.py"
echo "3. 1回だけ実行してテスト: python -m src.main"
echo "4. スケジューラーを開始: python run_scheduler.py"
echo
echo "📖 詳細なドキュメント:"
echo "- README.md: 基本的な使用方法"
echo "- docs/notion_setup.md: Notion連携の設定方法"
echo "- docs/scheduler_setup.md: スケジューラーの設定方法"
echo
echo "🔧 トラブルシューティング:"
echo "- python debug_tool.py: システム診断ツール"
echo "- python -m src.main --debug: デバッグモードで実行"