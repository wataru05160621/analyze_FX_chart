"""
Phase1 デモトレーダー AWS版
S3とDynamoDBを使用してクラウドネイティブに動作
"""
import asyncio
import json
import logging
import boto3
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import random
from decimal import Decimal
from pathlib import Path
import tempfile

from src.chart_generator import ChartGenerator
from src.claude_analyzer import ClaudeAnalyzer

logger = logging.getLogger(__name__)

class Phase1DemoTraderAWS:
    """AWS対応版デモトレーダー"""
    
    def __init__(self, s3_bucket: str, dynamodb_table: str):
        self.s3_bucket = s3_bucket
        self.dynamodb_table = dynamodb_table
        
        # AWS クライアント
        self.s3_client = boto3.client('s3')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(dynamodb_table)
        
        # 分析ツール
        self.chart_generator = ChartGenerator('USDJPY=X')
        self.analyzer = ClaudeAnalyzer()
        
        # アクティブトレード（メモリ内キャッシュ）
        self.active_trades = {}
        self.is_running = False
        self.start_time = datetime.now()
        
    async def start_trading(self):
        """24時間自動トレード"""
        self.is_running = True
        logger.info("AWS Phase1 デモトレード開始")
        
        # 起動時にアクティブトレードを復元
        await self._restore_active_trades()
        
        while self.is_running:
            try:
                # 現在の市場分析
                setup = await self.analyze_current_market()
                
                if setup and self.should_enter_trade(setup):
                    # エントリー実行
                    trade_id = await self.enter_trade(setup)
                    if trade_id:
                        logger.info(f"新規トレード: {trade_id}")
                
                # アクティブトレードの監視
                await self.monitor_active_trades()
                
                # ヘルスチェック更新
                await self._update_health_check()
                
                # 5分待機
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error(f"トレードループエラー: {e}")
                await asyncio.sleep(60)
    
    async def analyze_current_market(self) -> Optional[Dict]:
        """市場分析（チャートはS3に保存）"""
        try:
            # 一時ディレクトリでチャート生成
            with tempfile.TemporaryDirectory() as tmpdir:
                output_dir = Path(tmpdir) / 'charts'
                output_dir.mkdir()
                
                screenshots = self.chart_generator.generate_multiple_charts(
                    timeframes=['5min', '1hour'],
                    output_dir=output_dir,
                    candle_count=288
                )
                
                # S3にアップロード
                s3_screenshots = {}
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                
                for timeframe, local_path in screenshots.items():
                    s3_key = f"charts/{datetime.now().strftime('%Y/%m/%d')}/analysis_{timestamp}_{timeframe}.png"
                    self.s3_client.upload_file(str(local_path), self.s3_bucket, s3_key)
                    s3_screenshots[timeframe] = f"s3://{self.s3_bucket}/{s3_key}"
                    logger.info(f"チャートアップロード: {s3_key}")
                
                # Claude分析
                analysis = self.analyzer.analyze_charts(screenshots)
                
                # セットアップ情報を抽出
                setup = self._extract_setup_info(analysis, s3_screenshots)
                
                # 分析結果をS3に保存
                analysis_key = f"analysis/{datetime.now().strftime('%Y/%m/%d')}/analysis_{timestamp}.json"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=analysis_key,
                    Body=json.dumps({
                        'timestamp': timestamp,
                        'analysis': analysis,
                        'setup': setup,
                        'charts': s3_screenshots
                    }, ensure_ascii=False)
                )
                
                return setup
                
        except Exception as e:
            logger.error(f"市場分析エラー: {e}")
            return None
    
    def _extract_setup_info(self, analysis: str, screenshots: Dict) -> Optional[Dict]:
        """セットアップ情報抽出（元の実装と同じ）"""
        setup = {
            'timestamp': datetime.now().isoformat(),
            'analysis': analysis,
            'screenshots': screenshots,
            'setup_type': None,
            'entry_price': None,
            'confidence': 0,
            'signal_quality': 0
        }
        
        # セットアップタイプの検出
        if 'セットアップA' in analysis or 'パターンブレイク' in analysis:
            setup['setup_type'] = 'A'
        elif 'セットアップB' in analysis or 'プルバック' in analysis:
            setup['setup_type'] = 'B'
        
        # 品質スコアの抽出
        if '⭐⭐⭐⭐⭐' in analysis:
            setup['signal_quality'] = 5
            setup['confidence'] = 0.9
        elif '⭐⭐⭐⭐' in analysis:
            setup['signal_quality'] = 4
            setup['confidence'] = 0.75
        elif '⭐⭐⭐' in analysis:
            setup['signal_quality'] = 3
            setup['confidence'] = 0.6
        
        # エントリー価格の抽出
        import re
        price_match = re.search(r'エントリー[：:]\s*([\d.]+)', analysis)
        if price_match:
            setup['entry_price'] = float(price_match.group(1))
        
        return setup if setup['setup_type'] and setup['signal_quality'] >= 3 else None
    
    def should_enter_trade(self, setup: Dict) -> bool:
        """トレード判断（元の実装と同じ）"""
        if len(self.active_trades) >= 2:
            return False
        
        current_hour = datetime.now().hour
        if current_hour < 7 or current_hour > 22:
            return False
        
        if setup['signal_quality'] < 3:
            return False
        
        return True
    
    async def enter_trade(self, setup: Dict) -> Optional[str]:
        """トレードエントリー（DynamoDBに記録）"""
        try:
            current_price = setup['entry_price'] or self._get_current_price()
            trade_id = f"DEMO_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # DynamoDBに保存
            trade_item = {
                'trade_id': trade_id,
                'timestamp': datetime.now().isoformat(),
                'session': self._determine_session(),
                'setup_type': setup['setup_type'],
                'entry_price': Decimal(str(current_price)),
                'entry_time': datetime.now().isoformat(),
                'signal_quality': setup['signal_quality'],
                'tp_price': Decimal(str(current_price + 0.20)),
                'sl_price': Decimal(str(current_price - 0.10)),
                'status': 'active',
                'analysis_summary': setup['analysis'][:500],
                'confidence_score': Decimal(str(setup['confidence'])),
                'entry_chart_s3': setup['screenshots']['5min'],
                'ttl': int((datetime.now() + timedelta(days=90)).timestamp())  # 90日後に自動削除
            }
            
            self.table.put_item(Item=trade_item)
            
            # メモリキャッシュ更新
            self.active_trades[trade_id] = {
                'trade_id': trade_id,
                'entry_price': current_price,
                'entry_time': datetime.now(),
                'tp_price': current_price + 0.20,
                'sl_price': current_price - 0.10,
                'status': 'active',
                'mfe': 0,
                'mae': 0
            }
            
            # SNS通知
            await self._notify_trade_entry(trade_id, setup)
            
            return trade_id
            
        except Exception as e:
            logger.error(f"エントリーエラー: {e}")
            return None
    
    async def monitor_active_trades(self):
        """アクティブトレード監視"""
        current_price = self._get_current_price()
        
        for trade_id, trade_info in list(self.active_trades.items()):
            if trade_info['status'] != 'active':
                continue
            
            # TP/SLチェック
            if current_price >= trade_info['tp_price']:
                await self.exit_trade(trade_id, current_price, 'TP')
            elif current_price <= trade_info['sl_price']:
                await self.exit_trade(trade_id, current_price, 'SL')
            else:
                # MFE/MAE更新
                pips = (current_price - trade_info['entry_price']) * 100
                trade_info['mfe'] = max(trade_info['mfe'], pips)
                trade_info['mae'] = min(trade_info['mae'], pips)
    
    async def exit_trade(self, trade_id: str, exit_price: float, exit_reason: str):
        """トレード決済（DynamoDB更新）"""
        try:
            trade_info = self.active_trades[trade_id]
            
            # DynamoDB更新
            pips_result = (exit_price - trade_info['entry_price']) * 100
            
            self.table.update_item(
                Key={'trade_id': trade_id},
                UpdateExpression='SET #status = :status, exit_price = :exit_price, '
                               'exit_time = :exit_time, exit_reason = :exit_reason, '
                               'pips_result = :pips, max_favorable_excursion = :mfe, '
                               'max_adverse_excursion = :mae, time_in_trade = :duration',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'closed',
                    ':exit_price': Decimal(str(exit_price)),
                    ':exit_time': datetime.now().isoformat(),
                    ':exit_reason': exit_reason,
                    ':pips': Decimal(str(round(pips_result, 1))),
                    ':mfe': Decimal(str(trade_info['mfe'])),
                    ':mae': Decimal(str(trade_info['mae'])),
                    ':duration': int((datetime.now() - trade_info['entry_time']).total_seconds() / 60)
                }
            )
            
            # メモリから削除
            del self.active_trades[trade_id]
            
            # 結果通知
            await self._notify_trade_exit(trade_id, pips_result, exit_reason)
            
            logger.info(f"トレード決済: {trade_id} - {exit_reason} - {pips_result:.1f} pips")
            
        except Exception as e:
            logger.error(f"決済エラー: {e}")
    
    async def _restore_active_trades(self):
        """起動時にアクティブトレードを復元"""
        try:
            response = self.table.query(
                IndexName='status-index',
                KeyConditionExpression='#status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': 'active'}
            )
            
            for item in response.get('Items', []):
                self.active_trades[item['trade_id']] = {
                    'trade_id': item['trade_id'],
                    'entry_price': float(item['entry_price']),
                    'entry_time': datetime.fromisoformat(item['entry_time']),
                    'tp_price': float(item['tp_price']),
                    'sl_price': float(item['sl_price']),
                    'status': 'active',
                    'mfe': float(item.get('max_favorable_excursion', 0)),
                    'mae': float(item.get('max_adverse_excursion', 0))
                }
            
            logger.info(f"アクティブトレード復元: {len(self.active_trades)}件")
            
        except Exception as e:
            logger.error(f"トレード復元エラー: {e}")
    
    async def _update_health_check(self):
        """ヘルスチェック更新"""
        try:
            health_key = "health/demo_trader.json"
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=health_key,
                Body=json.dumps({
                    'timestamp': datetime.now().isoformat(),
                    'status': 'healthy',
                    'active_trades': len(self.active_trades),
                    'uptime_minutes': int((datetime.now() - self.start_time).total_seconds() / 60)
                })
            )
        except:
            pass
    
    async def _notify_trade_entry(self, trade_id: str, setup: Dict):
        """エントリー通知"""
        try:
            import os
            sns_client = boto3.client('sns')
            topic_arn = os.environ.get('SNS_TOPIC_ARN')
            
            if topic_arn:
                sns_client.publish(
                    TopicArn=topic_arn,
                    Subject='新規デモトレード',
                    Message=f"ID: {trade_id}\n"
                           f"セットアップ: {setup['setup_type']}\n"
                           f"品質: {'⭐' * setup['signal_quality']}\n"
                           f"信頼度: {setup['confidence']:.0%}"
                )
        except:
            pass
    
    async def _notify_trade_exit(self, trade_id: str, pips: float, reason: str):
        """決済通知"""
        try:
            import os
            sns_client = boto3.client('sns')
            topic_arn = os.environ.get('SNS_TOPIC_ARN')
            
            if topic_arn:
                emoji = '🟢' if pips > 0 else '🔴'
                sns_client.publish(
                    TopicArn=topic_arn,
                    Subject='デモトレード決済',
                    Message=f"{emoji} ID: {trade_id}\n"
                           f"結果: {pips:.1f} pips ({reason})"
                )
        except:
            pass
    
    def _get_current_price(self) -> float:
        """現在価格取得（TODO: 実装）"""
        base = 150.0
        return base + random.uniform(-1, 1)
    
    def _determine_session(self) -> str:
        """セッション判定"""
        hour = datetime.now().hour
        if 7 <= hour < 15:
            return "アジア"
        elif 15 <= hour < 21:
            return "ロンドン"
        else:
            return "NY"