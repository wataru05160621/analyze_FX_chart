# ローカルLLM比較ガイド

## Mac向け推奨構成

### 1. Ollama + LLaVA（最も簡単）

**セットアップ:**
```bash
# インストール
brew install ollama

# モデルダウンロード（約4.7GB）
ollama pull llava

# 実行
python3 execute_with_ollama.py
```

**必要スペック:**
- Mac M1以上（8GB RAM最小、16GB推奨）
- ストレージ: 10GB以上

**精度:** ★★★☆☆

### 2. MLX + LLaVA（Apple Silicon最適化）

**セットアップ:**
```bash
pip install mlx mlx-lm
# MLX版LLaVAモデルをダウンロード
```

**必要スペック:**
- Mac M1 Pro以上推奨
- RAM: 16GB以上

**精度:** ★★★★☆

## GPU搭載PC向け

### 1. LLaVA-1.5（標準）

**必要スペック:**
- GPU: RTX 3060 (12GB) 最小
- GPU: RTX 3090 (24GB) 推奨
- RAM: 32GB

**セットアップ:**
```bash
pip install transformers torch torchvision
# 7Bモデル: 約14GB
# 13Bモデル: 約26GB
```

**精度:** ★★★★☆

### 2. CogVLM（高精度）

**必要スペック:**
- GPU: RTX 4090 (24GB) 最小
- RAM: 64GB推奨

**精度:** ★★★★★

## クラウドGPU利用

### 1. Google Colab Pro+
- 月額約$50
- A100 40GB利用可能
- ノートブック形式で実行

### 2. RunPod
- 時間課金（$0.5-2/時間）
- RTX 4090/A100選択可能

## 実装済みソリューション

### 1. Ollama（今すぐ使える）
```bash
# セットアップ
./setup_ollama.sh

# 実行
python3 execute_with_ollama.py
```

### 2. Claude Web（API代替）
```bash
# Selenium必要
pip install selenium

# 実行（手動ログイン必要）
python3 execute_with_claude_web.py
```

### 3. API不要版（チャートのみ）
```bash
# 分析なしでチャート投稿
python3 execute_without_api.py
```

## コスト比較

| 方法 | 初期費用 | ランニングコスト | 品質 |
|------|---------|----------------|------|
| Claude API | $0 | $0.01-0.03/回 | ★★★★★ |
| Ollama (Mac) | $0 | 電気代のみ | ★★★☆☆ |
| RTX 3090 | $1,500 | 電気代のみ | ★★★★☆ |
| Claude Web | $0 | 無料（制限あり） | ★★★★★ |
| Colab Pro+ | $0 | $50/月 | ★★★★☆ |

## 推奨アプローチ

### 現在のMacで：
1. **即座に実行可能**: `execute_without_api.py`（チャートのみ）
2. **30分で準備可能**: Ollama + LLaVA
3. **手動だが高品質**: Claude Web版

### 将来的な改善：
1. 複数APIのフォールバック実装
2. ローカルLLMの精度向上待ち
3. Claude APIの負荷が下がるのを待つ

## 次のステップ

1. まず`execute_without_api.py`でチャート投稿
2. Ollamaをインストールして試す
3. API復旧を待ちながら代替手段を検討