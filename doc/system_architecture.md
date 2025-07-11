# FX自動分析システム アーキテクチャ

## システム全体構成

```mermaid
graph TB
    subgraph "AWS EventBridge"
        EB1[朝8:00トリガー]
        EB2[昼15:00トリガー]
        EB3[夜21:00トリガー]
    end

    subgraph "AWS ECS Fargate"
        ECS[FX分析タスク]
    end

    subgraph "データ取得"
        YF[yfinance API]
        CG[Chart Generator]
    end

    subgraph "AI分析"
        CA[Claude 3.5 Sonnet]
        BA[ブログ用分析]
        TA[トレード用分析]
    end

    subgraph "データ保存"
        S3[AWS S3<br/>チャート画像]
        NT[Notion<br/>分析結果DB]
    end

    subgraph "ブログ投稿（8:00のみ）"
        WP[WordPress<br/>記事投稿]
        TW[X (Twitter)<br/>要約投稿]
    end

    EB1 --> ECS
    EB2 --> ECS
    EB3 --> ECS
    
    ECS --> YF
    YF --> CG
    CG --> CA
    
    CA --> BA
    CA --> TA
    
    CG --> S3
    TA --> NT
    S3 --> NT
    
    BA --> WP
    WP --> TW
```

## 処理フロー詳細

```mermaid
sequenceDiagram
    participant EB as EventBridge
    participant ECS as ECS Fargate
    participant YF as yfinance
    participant CG as ChartGenerator
    participant Claude as Claude AI
    participant S3 as AWS S3
    participant Notion as Notion
    participant WP as WordPress
    participant X as X/Twitter

    EB->>ECS: 定時実行トリガー
    ECS->>YF: USD/JPY価格データ取得
    YF-->>ECS: 価格データ（OHLCV）
    
    ECS->>CG: チャート生成依頼
    Note over CG: 5分足・1時間足<br/>EMA(25,75,200)付き
    CG-->>ECS: チャート画像
    
    ECS->>S3: 画像アップロード
    S3-->>ECS: 画像URL
    
    ECS->>Claude: チャート分析依頼
    Note over Claude: Volmanメソッド<br/>に基づく分析
    Claude-->>ECS: 分析結果（2種類）
    
    ECS->>Notion: 通常分析結果保存
    Note over Notion: トレード用詳細分析
    
    alt 8:00実行時のみ
        ECS->>Claude: ブログ用分析生成
        Claude-->>ECS: 教育的分析
        ECS->>WP: 記事投稿
        WP-->>ECS: 記事URL
        ECS->>X: 要約投稿
        Note over X: 記事URLを含む
    end
```

## データフロー

```mermaid
graph LR
    subgraph "入力データ"
        YF1[USD/JPY価格]
        PDF[プライスアクション<br/>の原則.pdf]
    end

    subgraph "生成物"
        CH1[5分足チャート]
        CH2[1時間足チャート]
        AN1[通常分析<br/>（トレード用）]
        AN2[ブログ分析<br/>（教育用）]
    end

    subgraph "保存先"
        S3DB[(S3バケット<br/>画像保存)]
        NDB[(Notion DB<br/>分析記録)]
        WPDB[(WordPress<br/>ブログ記事)]
        XDB[(X/Twitter<br/>投稿)]
    end

    YF1 --> CH1
    YF1 --> CH2
    PDF --> AN1
    PDF --> AN2
    CH1 --> AN1
    CH2 --> AN1
    CH1 --> AN2
    CH2 --> AN2
    
    CH1 --> S3DB
    CH2 --> S3DB
    AN1 --> NDB
    S3DB --> NDB
    
    AN2 --> WPDB
    AN2 --> XDB
    WPDB --> XDB
```

## 環境構成

```mermaid
graph TB
    subgraph "開発環境"
        DEV[ローカル開発<br/>Python 3.11]
        VENV[仮想環境<br/>venv]
        ENV[.env設定]
    end

    subgraph "AWS本番環境"
        subgraph "コンピュート"
            FARGATE[ECS Fargate<br/>1vCPU/2GB]
        end
        
        subgraph "ストレージ"
            S3[S3バケット<br/>画像保存]
            SM[Secrets Manager<br/>API Keys]
        end
        
        subgraph "ネットワーク"
            VPC[VPC<br/>Public Subnet]
            SG[Security Group<br/>Egress Only]
        end
        
        subgraph "監視"
            CW[CloudWatch Logs]
            SNS[SNS Alerts]
        end
    end

    subgraph "外部サービス"
        CLAUDE[Claude API]
        NOTION[Notion API]
        WP[WordPress API]
        TWITTER[X API v1.1/v2]
        YAHOO[Yahoo Finance]
    end

    DEV --> FARGATE
    FARGATE --> S3
    FARGATE --> SM
    FARGATE --> VPC
    VPC --> SG
    FARGATE --> CW
    CW --> SNS
    
    FARGATE --> CLAUDE
    FARGATE --> NOTION
    FARGATE --> WP
    FARGATE --> TWITTER
    FARGATE --> YAHOO
```

## 実行スケジュール

```mermaid
gantt
    title 日次実行スケジュール（JST）
    dateFormat HH:mm
    axisFormat %H:%M
    
    section 平日のみ
    朝の分析（ブログ投稿）  :active, morning, 08:00, 30m
    昼の分析              :afternoon, 15:00, 30m
    夜の分析              :evening, 21:00, 30m
    
    section 処理内容
    チャート生成          :5m
    AI分析               :10m
    Notion保存           :5m
    ブログ投稿(8:00のみ)  :10m
```

## エラーハンドリング

```mermaid
graph TD
    START[処理開始] --> TRY{処理実行}
    TRY -->|成功| SUCCESS[正常終了]
    TRY -->|エラー| ERROR[エラー処理]
    
    ERROR --> LOG[CloudWatch<br/>ログ記録]
    ERROR --> RETRY{リトライ可能?}
    
    RETRY -->|Yes| RETRY_EXEC[再実行<br/>最大3回]
    RETRY -->|No| ALERT[SNSアラート]
    
    RETRY_EXEC --> TRY
    
    ALERT --> FAIL[タスク失敗]
    LOG --> CONTINUE[処理継続]
    
    style ERROR fill:#f99
    style ALERT fill:#f99
    style FAIL fill:#f99
    style SUCCESS fill:#9f9
```

## 通貨ペア拡張計画

```mermaid
graph LR
    subgraph "現在"
        USD1[USD/JPY]
    end
    
    subgraph "Phase 1"
        USD2[USD/JPY]
        GOLD[XAU/USD]
        BTC[BTC/USD]
    end
    
    subgraph "Phase 2"
        USD3[USD/JPY]
        GOLD2[XAU/USD]
        BTC2[BTC/USD]
        EUR[EUR/USD]
        GBP[GBP/USD]
    end
    
    USD1 --> USD2
    USD2 --> USD3
    GOLD --> GOLD2
    BTC --> BTC2
    
    style USD1 fill:#9f9
    style USD2 fill:#9f9
    style GOLD fill:#ff9
    style BTC fill:#ff9
```