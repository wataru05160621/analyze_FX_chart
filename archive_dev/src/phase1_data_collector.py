"""
Phase1 検証データ収集モジュール
トレード結果と市場データを体系的に保存
"""
import os
import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import pandas as pd
from dataclasses import dataclass, asdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class TradeRecord:
    """トレード記録のデータ構造"""
    # 基本情報
    trade_id: str
    timestamp: str
    session: str  # アジア/ロンドン/NY
    
    # エントリー情報
    setup_type: str  # A-F
    entry_price: float
    entry_time: str
    signal_quality: int  # 1-5の品質評価
    
    # ビルドアップ情報
    buildup_duration: int  # 分
    buildup_pattern: str  # 三角保ち合い、フラッグ等
    ema_configuration: str  # 上昇配列、下降配列、混在
    
    # 市場環境
    atr_at_entry: float
    spread_at_entry: float
    volatility_level: str  # 高/中/低
    news_nearby: bool
    
    # 結果
    exit_price: float
    exit_time: str
    exit_reason: str  # TP/SL/手動
    pips_result: float
    profit_loss: float
    
    # 追加分析
    max_favorable_excursion: float  # 最大含み益
    max_adverse_excursion: float  # 最大含み損
    time_in_trade: int  # 分
    
    # チャート画像
    entry_chart_path: str
    exit_chart_path: str
    
    # AI分析
    ai_analysis_summary: str
    confidence_score: float

@dataclass
class MarketSnapshot:
    """市場スナップショット"""
    timestamp: str
    price: float
    ema_25: float
    ema_75: float
    ema_200: float
    atr: float
    spread: float
    volume: Optional[float]
    session: str
    major_news: List[str]

class Phase1DataCollector:
    """Phase1検証データ収集クラス"""
    
    def __init__(self, data_dir: str = "phase1_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # データベース初期化
        self.db_path = self.data_dir / "phase1_trades.db"
        self._init_database()
        
        # JSONバックアップディレクトリ
        self.json_backup_dir = self.data_dir / "json_backups"
        self.json_backup_dir.mkdir(exist_ok=True)
        
        # チャート画像ディレクトリ
        self.charts_dir = self.data_dir / "trade_charts"
        self.charts_dir.mkdir(exist_ok=True)
        
    def _init_database(self):
        """SQLiteデータベース初期化"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # トレード記録テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                trade_id TEXT PRIMARY KEY,
                timestamp TIMESTAMP,
                session TEXT,
                setup_type TEXT,
                entry_price REAL,
                entry_time TIMESTAMP,
                signal_quality INTEGER,
                buildup_duration INTEGER,
                buildup_pattern TEXT,
                ema_configuration TEXT,
                atr_at_entry REAL,
                spread_at_entry REAL,
                volatility_level TEXT,
                news_nearby BOOLEAN,
                exit_price REAL,
                exit_time TIMESTAMP,
                exit_reason TEXT,
                pips_result REAL,
                profit_loss REAL,
                max_favorable_excursion REAL,
                max_adverse_excursion REAL,
                time_in_trade INTEGER,
                entry_chart_path TEXT,
                exit_chart_path TEXT,
                ai_analysis_summary TEXT,
                confidence_score REAL
            )
        """)
        
        # 市場スナップショットテーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP,
                price REAL,
                ema_25 REAL,
                ema_75 REAL,
                ema_200 REAL,
                atr REAL,
                spread REAL,
                volume REAL,
                session TEXT,
                major_news TEXT
            )
        """)
        
        # パフォーマンス統計テーブル
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS performance_stats (
                date DATE PRIMARY KEY,
                total_trades INTEGER,
                winning_trades INTEGER,
                losing_trades INTEGER,
                win_rate REAL,
                total_pips REAL,
                profit_factor REAL,
                max_drawdown REAL,
                average_win REAL,
                average_loss REAL,
                best_setup_type TEXT,
                worst_setup_type TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_trade(self, trade: TradeRecord):
        """トレード記録を保存"""
        try:
            # SQLiteに保存
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            trade_dict = asdict(trade)
            columns = ', '.join(trade_dict.keys())
            placeholders = ', '.join(['?' for _ in trade_dict])
            
            cursor.execute(
                f"INSERT OR REPLACE INTO trades ({columns}) VALUES ({placeholders})",
                list(trade_dict.values())
            )
            
            conn.commit()
            conn.close()
            
            # JSONバックアップ
            json_path = self.json_backup_dir / f"trade_{trade.trade_id}.json"
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(trade_dict, f, ensure_ascii=False, indent=2)
            
            logger.info(f"トレード記録保存: {trade.trade_id}")
            
        except Exception as e:
            logger.error(f"トレード保存エラー: {e}")
    
    def save_market_snapshot(self, snapshot: MarketSnapshot):
        """市場スナップショットを保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO market_snapshots 
                (timestamp, price, ema_25, ema_75, ema_200, atr, spread, volume, session, major_news)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                snapshot.timestamp,
                snapshot.price,
                snapshot.ema_25,
                snapshot.ema_75,
                snapshot.ema_200,
                snapshot.atr,
                snapshot.spread,
                snapshot.volume,
                snapshot.session,
                json.dumps(snapshot.major_news)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"市場スナップショット保存エラー: {e}")
    
    def calculate_daily_stats(self, date: str):
        """日次統計を計算して保存"""
        try:
            conn = sqlite3.connect(self.db_path)
            
            # 該当日のトレードを取得
            df = pd.read_sql_query(
                "SELECT * FROM trades WHERE DATE(entry_time) = ?",
                conn,
                params=[date]
            )
            
            if len(df) == 0:
                return
            
            # 統計計算
            stats = {
                'date': date,
                'total_trades': len(df),
                'winning_trades': len(df[df['pips_result'] > 0]),
                'losing_trades': len(df[df['pips_result'] < 0]),
                'win_rate': len(df[df['pips_result'] > 0]) / len(df) * 100,
                'total_pips': df['pips_result'].sum(),
                'profit_factor': self._calculate_profit_factor(df),
                'max_drawdown': self._calculate_max_drawdown(df),
                'average_win': df[df['pips_result'] > 0]['pips_result'].mean() if len(df[df['pips_result'] > 0]) > 0 else 0,
                'average_loss': df[df['pips_result'] < 0]['pips_result'].mean() if len(df[df['pips_result'] < 0]) > 0 else 0,
                'best_setup_type': self._find_best_setup(df),
                'worst_setup_type': self._find_worst_setup(df)
            }
            
            # 保存
            cursor = conn.cursor()
            columns = ', '.join(stats.keys())
            placeholders = ', '.join(['?' for _ in stats])
            
            cursor.execute(
                f"INSERT OR REPLACE INTO performance_stats ({columns}) VALUES ({placeholders})",
                list(stats.values())
            )
            
            conn.commit()
            conn.close()
            
            # CSVエクスポート
            self._export_daily_csv(date, df, stats)
            
        except Exception as e:
            logger.error(f"日次統計計算エラー: {e}")
    
    def _calculate_profit_factor(self, df: pd.DataFrame) -> float:
        """プロフィットファクター計算"""
        wins = df[df['pips_result'] > 0]['pips_result'].sum()
        losses = abs(df[df['pips_result'] < 0]['pips_result'].sum())
        return wins / losses if losses > 0 else float('inf')
    
    def _calculate_max_drawdown(self, df: pd.DataFrame) -> float:
        """最大ドローダウン計算"""
        df = df.sort_values('entry_time')
        cumulative = df['pips_result'].cumsum()
        running_max = cumulative.expanding().max()
        drawdown = cumulative - running_max
        return drawdown.min()
    
    def _find_best_setup(self, df: pd.DataFrame) -> str:
        """最も成績の良いセットアップを特定"""
        setup_performance = df.groupby('setup_type')['pips_result'].sum()
        return setup_performance.idxmax() if len(setup_performance) > 0 else 'N/A'
    
    def _find_worst_setup(self, df: pd.DataFrame) -> str:
        """最も成績の悪いセットアップを特定"""
        setup_performance = df.groupby('setup_type')['pips_result'].sum()
        return setup_performance.idxmin() if len(setup_performance) > 0 else 'N/A'
    
    def _export_daily_csv(self, date: str, trades_df: pd.DataFrame, stats: Dict):
        """日次データをCSVエクスポート"""
        csv_dir = self.data_dir / "daily_reports"
        csv_dir.mkdir(exist_ok=True)
        
        # トレード詳細
        trades_csv = csv_dir / f"trades_{date}.csv"
        trades_df.to_csv(trades_csv, index=False)
        
        # 統計サマリー
        stats_csv = csv_dir / f"stats_{date}.csv"
        pd.DataFrame([stats]).to_csv(stats_csv, index=False)
    
    def get_performance_summary(self, start_date: str, end_date: str) -> Dict:
        """期間のパフォーマンスサマリーを取得"""
        conn = sqlite3.connect(self.db_path)
        
        # トレードデータ取得
        trades_df = pd.read_sql_query(
            "SELECT * FROM trades WHERE DATE(entry_time) BETWEEN ? AND ?",
            conn,
            params=[start_date, end_date]
        )
        
        # 統計データ取得
        stats_df = pd.read_sql_query(
            "SELECT * FROM performance_stats WHERE date BETWEEN ? AND ?",
            conn,
            params=[start_date, end_date]
        )
        
        conn.close()
        
        # サマリー作成
        summary = {
            'period': f"{start_date} to {end_date}",
            'total_trades': len(trades_df),
            'total_pips': trades_df['pips_result'].sum(),
            'average_daily_trades': len(trades_df) / len(stats_df) if len(stats_df) > 0 else 0,
            'overall_win_rate': len(trades_df[trades_df['pips_result'] > 0]) / len(trades_df) * 100 if len(trades_df) > 0 else 0,
            'best_day': stats_df.loc[stats_df['total_pips'].idxmax()]['date'] if len(stats_df) > 0 else 'N/A',
            'worst_day': stats_df.loc[stats_df['total_pips'].idxmin()]['date'] if len(stats_df) > 0 else 'N/A',
            'setup_performance': self._analyze_setup_performance(trades_df),
            'session_performance': self._analyze_session_performance(trades_df),
            'buildup_pattern_performance': self._analyze_buildup_patterns(trades_df)
        }
        
        return summary
    
    def _analyze_setup_performance(self, df: pd.DataFrame) -> Dict:
        """セットアップ別パフォーマンス分析"""
        if len(df) == 0:
            return {}
        
        setup_stats = {}
        for setup in df['setup_type'].unique():
            setup_df = df[df['setup_type'] == setup]
            setup_stats[setup] = {
                'count': len(setup_df),
                'win_rate': len(setup_df[setup_df['pips_result'] > 0]) / len(setup_df) * 100,
                'total_pips': setup_df['pips_result'].sum(),
                'average_pips': setup_df['pips_result'].mean()
            }
        
        return setup_stats
    
    def _analyze_session_performance(self, df: pd.DataFrame) -> Dict:
        """セッション別パフォーマンス分析"""
        if len(df) == 0:
            return {}
        
        session_stats = {}
        for session in df['session'].unique():
            session_df = df[df['session'] == session]
            session_stats[session] = {
                'count': len(session_df),
                'win_rate': len(session_df[session_df['pips_result'] > 0]) / len(session_df) * 100,
                'total_pips': session_df['pips_result'].sum(),
                'average_pips': session_df['pips_result'].mean()
            }
        
        return session_stats
    
    def _analyze_buildup_patterns(self, df: pd.DataFrame) -> Dict:
        """ビルドアップパターン別分析"""
        if len(df) == 0:
            return {}
        
        pattern_stats = {}
        for pattern in df['buildup_pattern'].unique():
            pattern_df = df[df['buildup_pattern'] == pattern]
            pattern_stats[pattern] = {
                'count': len(pattern_df),
                'win_rate': len(pattern_df[pattern_df['pips_result'] > 0]) / len(pattern_df) * 100,
                'average_quality': pattern_df['signal_quality'].mean()
            }
        
        return pattern_stats
    
    def export_for_ml_training(self, output_path: str):
        """機械学習用データセットをエクスポート"""
        conn = sqlite3.connect(self.db_path)
        
        # 全トレードデータ取得
        trades_df = pd.read_sql_query("SELECT * FROM trades", conn)
        
        # 特徴量エンジニアリング
        features_df = pd.DataFrame({
            # 基本特徴量
            'setup_type_encoded': pd.Categorical(trades_df['setup_type']).codes,
            'session_encoded': pd.Categorical(trades_df['session']).codes,
            'signal_quality': trades_df['signal_quality'],
            'buildup_duration': trades_df['buildup_duration'],
            'atr_at_entry': trades_df['atr_at_entry'],
            'spread_at_entry': trades_df['spread_at_entry'],
            'volatility_encoded': pd.Categorical(trades_df['volatility_level']).codes,
            'news_nearby': trades_df['news_nearby'].astype(int),
            
            # EMA特徴量
            'ema_config_encoded': pd.Categorical(trades_df['ema_configuration']).codes,
            
            # ターゲット
            'pips_result': trades_df['pips_result'],
            'is_winner': (trades_df['pips_result'] > 0).astype(int)
        })
        
        # 保存
        features_df.to_csv(output_path, index=False)
        conn.close()
        
        logger.info(f"ML用データセットエクスポート完了: {output_path}")

# 使用例
if __name__ == "__main__":
    collector = Phase1DataCollector()
    
    # トレード記録の例
    trade = TradeRecord(
        trade_id="TRADE_20240315_001",
        timestamp=datetime.now().isoformat(),
        session="アジア",
        setup_type="A",
        entry_price=150.123,
        entry_time=datetime.now().isoformat(),
        signal_quality=4,
        buildup_duration=45,
        buildup_pattern="三角保ち合い",
        ema_configuration="上昇配列",
        atr_at_entry=8.5,
        spread_at_entry=1.2,
        volatility_level="中",
        news_nearby=False,
        exit_price=150.323,
        exit_time=datetime.now().isoformat(),
        exit_reason="TP",
        pips_result=20.0,
        profit_loss=2000.0,
        max_favorable_excursion=25.0,
        max_adverse_excursion=-5.0,
        time_in_trade=35,
        entry_chart_path="charts/entry_001.png",
        exit_chart_path="charts/exit_001.png",
        ai_analysis_summary="良好なビルドアップからの明確なブレイク",
        confidence_score=0.85
    )
    
    collector.save_trade(trade)