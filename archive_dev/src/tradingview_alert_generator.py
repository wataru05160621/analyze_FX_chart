"""
TradingViewアラート設定生成（半自動化）
Phase 1の分析結果からTradingViewアラート設定を自動生成
"""
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Optional
import os
from datetime import datetime
import json


class AlertType(Enum):
    """アラートタイプ"""
    ENTRY = auto()
    STOP_LOSS = auto()
    TAKE_PROFIT = auto()


@dataclass
class AlertConfiguration:
    """アラート設定データクラス"""
    action: str  # BUY or SELL
    currency_pair: str  # e.g., USD/JPY
    entry_price: float
    stop_loss: float
    take_profit: float
    confidence: float
    
    def __post_init__(self):
        """初期化後の検証"""
        self._validate()
        
    @property
    def tv_symbol(self) -> str:
        """TradingView用のシンボル（スラッシュなし）"""
        return self.currency_pair.replace('/', '')
    
    def _validate(self):
        """設定の妥当性を検証"""
        if self.action == 'BUY':
            if self.stop_loss >= self.entry_price:
                raise ValueError("買い注文の損切りはエントリー価格より低い必要があります")
            if self.take_profit <= self.entry_price:
                raise ValueError("買い注文の利確はエントリー価格より高い必要があります")
        elif self.action == 'SELL':
            if self.stop_loss <= self.entry_price:
                raise ValueError("売り注文の損切りはエントリー価格より高い必要があります")
            if self.take_profit >= self.entry_price:
                raise ValueError("売り注文の利確はエントリー価格より低い必要があります")
    
    @classmethod
    def from_phase1_signal(cls, signal: Dict, currency_pair: str) -> 'AlertConfiguration':
        """Phase 1のシグナルから設定を作成"""
        return cls(
            action=signal['action'],
            currency_pair=currency_pair,
            entry_price=signal['entry_price'],
            stop_loss=signal['stop_loss'],
            take_profit=signal['take_profit'],
            confidence=signal['confidence']
        )


class TradingViewAlertGenerator:
    """TradingViewアラート設定生成クラス"""
    
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.environ.get(
            'TRADINGVIEW_WEBHOOK_URL',
            'https://your-domain.com/webhook/tradingview'
        )
    
    def generate_alert(self, config: AlertConfiguration, alert_type: AlertType) -> Dict:
        """個別のアラートを生成"""
        
        if alert_type == AlertType.ENTRY:
            return self._generate_entry_alert(config)
        elif alert_type == AlertType.STOP_LOSS:
            return self._generate_stop_loss_alert(config)
        elif alert_type == AlertType.TAKE_PROFIT:
            return self._generate_take_profit_alert(config)
    
    def _generate_entry_alert(self, config: AlertConfiguration) -> Dict:
        """エントリーアラートを生成"""
        if config.action == 'BUY':
            condition = f"{config.tv_symbol} >= {config.entry_price:.2f}"
            name = f"{config.currency_pair} 買いエントリー"
        else:
            condition = f"{config.tv_symbol} <= {config.entry_price:.2f}"
            name = f"{config.currency_pair} 売りエントリー"
        
        message = (
            f"{config.action} {config.tv_symbol} @ {{{{close}}}} "
            f"(Target: {config.take_profit:.2f}, SL: {config.stop_loss:.2f})"
        )
        
        return {
            'name': name,
            'condition': condition,
            'message': message,
            'webhook_enabled': True,
            'alert_type': 'ENTRY'
        }
    
    def _generate_stop_loss_alert(self, config: AlertConfiguration) -> Dict:
        """損切りアラートを生成"""
        if config.action == 'BUY':
            condition = f"{config.tv_symbol} <= {config.stop_loss:.2f}"
        else:
            condition = f"{config.tv_symbol} >= {config.stop_loss:.2f}"
        
        message = f"STOP LOSS {config.tv_symbol} @ {{{{close}}}}"
        
        return {
            'name': f"{config.currency_pair} 損切り",
            'condition': condition,
            'message': message,
            'webhook_enabled': True,
            'alert_type': 'STOP_LOSS'
        }
    
    def _generate_take_profit_alert(self, config: AlertConfiguration) -> Dict:
        """利確アラートを生成"""
        if config.action == 'BUY':
            condition = f"{config.tv_symbol} >= {config.take_profit:.2f}"
        else:
            condition = f"{config.tv_symbol} <= {config.take_profit:.2f}"
        
        message = f"TAKE PROFIT {config.tv_symbol} @ {{{{close}}}}"
        
        return {
            'name': f"{config.currency_pair} 利確",
            'condition': condition,
            'message': message,
            'webhook_enabled': True,
            'alert_type': 'TAKE_PROFIT'
        }
    
    def generate_all_alerts(self, config: AlertConfiguration) -> List[Dict]:
        """全てのアラートを生成"""
        return [
            self.generate_alert(config, AlertType.ENTRY),
            self.generate_alert(config, AlertType.STOP_LOSS),
            self.generate_alert(config, AlertType.TAKE_PROFIT)
        ]
    
    def export_instructions(self, alerts: List[Dict], config: AlertConfiguration) -> str:
        """設定手順を文字列として出力"""
        instructions = []
        instructions.append("="*60)
        instructions.append("TradingViewアラート設定手順")
        instructions.append("="*60)
        instructions.append("")
        instructions.append(f"1. TradingViewで FX:{config.tv_symbol} チャートを開く")
        instructions.append("   https://jp.tradingview.com/chart/")
        instructions.append("")
        
        for i, alert in enumerate(alerts, 1):
            instructions.append(f"【アラート {i}】{alert['name']}")
            instructions.append("2. アラートアイコン（ベルマーク）をクリック")
            instructions.append("3. 以下を設定:")
            instructions.append(f"   - 条件: {alert['condition']}")
            instructions.append(f"   - アラート名: {alert['name']}")
            instructions.append(f"   - メッセージ: {alert['message']}")
            
            if alert['webhook_enabled']:
                instructions.append(f"   - Webhook URL: {self.webhook_url}")
                instructions.append("     ※「Webhook URL」にチェックを入れる")
            
            instructions.append("4. 「作成」をクリック")
            instructions.append("")
        
        instructions.append("="*60)
        instructions.append(f"設定生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        instructions.append(f"信頼度: {config.confidence:.1%}")
        instructions.append("="*60)
        
        return "\n".join(instructions)
    
    def _format_webhook_message(self, action: str, symbol: str, price: str, alert_type: AlertType) -> str:
        """Webhookメッセージをフォーマット"""
        data = {
            "action": action,
            "symbol": symbol,
            "price": price,
            "alert_type": alert_type.name,
            "timestamp": "{{time}}"
        }
        return json.dumps(data, indent=2).replace('"{{', '{{').replace('}}"', '}}')


class PineScriptGenerator:
    """Pine Script生成クラス"""
    
    def generate_script(self, config: AlertConfiguration) -> str:
        """Pine Scriptを生成"""
        script_lines = [
            "// This source code is subject to the terms of the Mozilla Public License 2.0",
            "// © Phase1_FX_Analysis",
            "",
            "//@version=5",
            f'indicator("FX Alert - {config.currency_pair}", overlay=true)',
            "",
            "// 設定値",
            f"entry_price = {config.entry_price:.2f}",
            f"stop_loss = {config.stop_loss:.2f}",
            f"take_profit = {config.take_profit:.2f}",
            "",
            "// 価格レベルを描画",
            'plot(entry_price, "Entry", color=color.blue, linewidth=2, style=plot.style_line)',
            'plot(stop_loss, "Stop Loss", color=color.red, linewidth=2, style=plot.style_line)',
            'plot(take_profit, "Take Profit", color=color.green, linewidth=2, style=plot.style_line)',
            "",
            "// 現在価格との関係をラベル表示",
            'if barstate.islast',
            '    label.new(bar_index, entry_price, "Entry: " + str.tostring(entry_price), ',
            '              style=label.style_label_left, color=color.blue, textcolor=color.white)',
            '    label.new(bar_index, stop_loss, "SL: " + str.tostring(stop_loss), ',
            '              style=label.style_label_left, color=color.red, textcolor=color.white)',
            '    label.new(bar_index, take_profit, "TP: " + str.tostring(take_profit), ',
            '              style=label.style_label_left, color=color.green, textcolor=color.white)',
            "",
            "// アラート条件",
            self._generate_alert_conditions(config),
            "",
            "// 背景色で状態を表示",
            "entry_zone = " + self._get_entry_zone_condition(config),
            "sl_zone = " + self._get_sl_zone_condition(config),
            "tp_zone = " + self._get_tp_zone_condition(config),
            "",
            "bgcolor(entry_zone ? color.new(color.blue, 90) : na)",
            "bgcolor(sl_zone ? color.new(color.red, 90) : na)",
            "bgcolor(tp_zone ? color.new(color.green, 90) : na)"
        ]
        
        return "\n".join(script_lines)
    
    def _generate_alert_conditions(self, config: AlertConfiguration) -> str:
        """アラート条件を生成"""
        conditions = []
        
        if config.action == 'BUY':
            conditions.extend([
                "// 買いシグナルのアラート条件",
                "entry_condition = close >= entry_price and close[1] < entry_price",
                "sl_condition = close <= stop_loss and close[1] > stop_loss",
                "tp_condition = close >= take_profit and close[1] < take_profit"
            ])
        else:
            conditions.extend([
                "// 売りシグナルのアラート条件",
                "entry_condition = close <= entry_price and close[1] > entry_price",
                "sl_condition = close >= stop_loss and close[1] < stop_loss",
                "tp_condition = close <= take_profit and close[1] > take_profit"
            ])
        
        conditions.extend([
            "",
            "// アラート設定",
            'if entry_condition',
            f'    alert("{config.action} Entry triggered at " + str.tostring(close), alert.freq_once_per_bar)',
            "",
            'if sl_condition',
            '    alert("Stop Loss hit at " + str.tostring(close), alert.freq_once_per_bar)',
            "",
            'if tp_condition',
            '    alert("Take Profit hit at " + str.tostring(close), alert.freq_once_per_bar)'
        ])
        
        return "\n".join(conditions)
    
    def _get_entry_zone_condition(self, config: AlertConfiguration) -> str:
        """エントリーゾーン条件"""
        if config.action == 'BUY':
            return f"close >= {config.entry_price * 0.999} and close <= {config.entry_price * 1.001}"
        else:
            return f"close <= {config.entry_price * 1.001} and close >= {config.entry_price * 0.999}"
    
    def _get_sl_zone_condition(self, config: AlertConfiguration) -> str:
        """損切りゾーン条件"""
        if config.action == 'BUY':
            return f"close <= {config.stop_loss * 1.001}"
        else:
            return f"close >= {config.stop_loss * 0.999}"
    
    def _get_tp_zone_condition(self, config: AlertConfiguration) -> str:
        """利確ゾーン条件"""
        if config.action == 'BUY':
            return f"close >= {config.take_profit * 0.999}"
        else:
            return f"close <= {config.take_profit * 1.001}"
    
    def save_script(self, script: str, filepath: Optional[str] = None) -> str:
        """スクリプトをファイルに保存"""
        if filepath is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filepath = f"tradingview_alert_{timestamp}.pine"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(script)
        
        return filepath