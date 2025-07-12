# FX分析の代替手法

## 1. Web版Claude/ChatGPTの活用

### Claude.ai (Web版)
```python
# src/claude_web_analyzer.py を作成可能
# Selenium/Playwrightで自動化
# - ログイン
# - 画像アップロード
# - 分析結果取得
```

**メリット**:
- API制限なし
- 最新モデル利用可能
- 無料プランでも利用可能

**デメリット**:
- 自動化が複雑
- アカウント制限の可能性
- レート制限あり

### ChatGPT Web版
既存の`src/chatgpt_web_analyzer.py`を活用可能

**実装例**:
```python
from src.chatgpt_web_analyzer import ChatGPTWebAnalyzer

analyzer = ChatGPTWebAnalyzer()
analysis = analyzer.analyze_charts_via_web(screenshots)
```

## 2. Claude CLI (コマンドライン版)

### インストール
```bash
pip install anthropic-cli
# または
brew install anthropic-cli
```

### 使用例
```bash
# 画像分析
claude analyze image.png --prompt "FXチャートを分析してください"
```

### Pythonからの実行
```python
import subprocess

def analyze_with_cli(image_path):
    cmd = [
        'claude', 'analyze', image_path,
        '--prompt', 'FXチャートの詳細な分析を行ってください'
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    return result.stdout
```

## 3. ローカルLLMでの分析

### 必要スペック（Claude相当の品質）

#### 最小要件
- **GPU**: RTX 3090 (24GB VRAM) または RTX 4090
- **RAM**: 32GB以上
- **ストレージ**: 100GB以上の空き容量

#### 推奨スペック
- **GPU**: RTX 4090 (24GB) × 2 または A100 (40GB)
- **RAM**: 64GB以上
- **CPU**: Intel i9 / AMD Ryzen 9

### 推奨モデル

#### 1. LLaVA (Vision対応)
```bash
# インストール
pip install llava

# 13Bモデル（RTX 3090で動作可能）
python -m llava.serve.cli \
    --model-path liuhaotian/llava-v1.5-13b \
    --image-file chart.png
```

#### 2. Qwen-VL (Alibaba)
```python
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained(
    "Qwen/Qwen-VL-Chat",
    device_map="auto",
    trust_remote_code=True
).eval()
```

#### 3. CogVLM
```bash
# 17Bパラメータ、高品質な画像理解
pip install cogvlm
```

### MacでのローカルLLM

#### Apple Silicon (M1/M2/M3)
```bash
# Ollama を使用
brew install ollama

# LLaVAモデルを実行
ollama run llava

# Pythonから使用
import ollama
response = ollama.chat(
    model='llava',
    messages=[{
        'role': 'user',
        'content': 'このチャートを分析してください',
        'images': ['chart.png']
    }]
)
```

**M1/M2 Macの場合**:
- M1 Max (32GB): 7B-13Bモデル実行可能
- M2 Ultra (192GB): 30B-70Bモデル実行可能

## 4. 実装可能な代替スクリプト

### Web版Claude自動化
```python
# execute_with_claude_web.py
from playwright.sync_api import sync_playwright

def analyze_with_claude_web(image_path):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Claude.aiにログイン
        page.goto("https://claude.ai")
        # ... ログイン処理
        
        # 画像アップロードと分析
        # ... 実装
        
        return analysis_text
```

### ローカルLLM統合
```python
# execute_with_local_llm.py
import torch
from PIL import Image
from transformers import LlavaForConditionalGeneration, AutoProcessor

def analyze_with_local_llm(image_path):
    # モデル読み込み（初回のみ遅い）
    model = LlavaForConditionalGeneration.from_pretrained(
        "llava-hf/llava-1.5-7b-hf"
    )
    processor = AutoProcessor.from_pretrained(
        "llava-hf/llava-1.5-7b-hf"
    )
    
    # 画像分析
    image = Image.open(image_path)
    prompt = "Analyze this forex chart in detail"
    inputs = processor(prompt, image, return_tensors="pt")
    
    # 推論
    output = model.generate(**inputs, max_new_tokens=1000)
    return processor.decode(output[0], skip_special_tokens=True)
```

## 5. コスト比較

| 方法 | 初期コスト | ランニングコスト | 品質 |
|------|-----------|----------------|------|
| Claude API | $0 | $0.01-0.03/分析 | ★★★★★ |
| Web版自動化 | $0 | $0（制限あり） | ★★★★★ |
| ローカルLLM (RTX 3090) | $1,500-2,000 | 電気代のみ | ★★★☆☆ |
| ローカルLLM (RTX 4090) | $2,000-2,500 | 電気代のみ | ★★★★☆ |
| Mac M2 Ultra | $6,000+ | 電気代のみ | ★★★★☆ |

## 6. 即座に実装可能な解決策

### ChatGPT Web版の活用
```bash
# 既存のchatgpt_web_analyzerを使用
python3 execute_with_chatgpt_web.py
```

### Ollamaでのローカル実行（Mac）
```bash
# インストール
brew install ollama

# モデルダウンロード
ollama pull llava

# 実行
python3 execute_with_ollama.py
```

## 推奨アプローチ

1. **短期的**: Web版自動化（Claude.ai/ChatGPT）
2. **中期的**: 複数APIのフォールバック実装
3. **長期的**: ローカルLLM環境構築（コスト削減）

現在のMacのスペックを教えていただければ、最適なローカルLLMを提案できます。