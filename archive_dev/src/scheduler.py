"""
定時実行スケジューラーモジュール
"""
import asyncio
import logging
from datetime import datetime, time
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from .main import analyze_fx_charts

logger = logging.getLogger(__name__)

class FXAnalysisScheduler:
    """FX分析の定時実行スケジューラー"""
    
    def __init__(self):
        # 日本時間のタイムゾーンを設定
        self.timezone = pytz.timezone('Asia/Tokyo')
        self.scheduler = AsyncIOScheduler(timezone=self.timezone)
        
        # 実行時刻の設定（日本時間）
        self.schedule_times = [
            {"hour": 8, "minute": 0},   # 8:00 AM JST
            {"hour": 15, "minute": 0},  # 3:00 PM JST
            {"hour": 21, "minute": 0}   # 9:00 PM JST
        ]
        
    def setup_jobs(self):
        """ジョブを設定"""
        for schedule_time in self.schedule_times:
            trigger = CronTrigger(
                hour=schedule_time["hour"],
                minute=schedule_time["minute"],
                timezone=self.timezone
            )
            
            self.scheduler.add_job(
                self._run_analysis,
                trigger=trigger,
                id=f"fx_analysis_{schedule_time['hour']:02d}{schedule_time['minute']:02d}",
                name=f"FX分析 {schedule_time['hour']:02d}:{schedule_time['minute']:02d} JST",
                replace_existing=True
            )
            
            logger.info(f"ジョブを設定: {schedule_time['hour']:02d}:{schedule_time['minute']:02d} JST")
            
    async def _run_analysis(self):
        """分析を実行"""
        try:
            current_time = datetime.now(self.timezone)
            logger.info(f"定時分析を開始: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            
            # 分析を実行
            result = await analyze_fx_charts()
            
            if result["status"] == "success":
                logger.info("定時分析が正常に完了しました")
            else:
                logger.error(f"定時分析でエラーが発生: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"定時分析中に予期しないエラーが発生: {e}", exc_info=True)
            
    def start(self):
        """スケジューラーを開始"""
        self.setup_jobs()
        self.scheduler.start()
        logger.info("スケジューラーを開始しました")
        
        # 次回実行時刻を表示
        self._show_next_runs()
        
    def stop(self):
        """スケジューラーを停止"""
        self.scheduler.shutdown()
        logger.info("スケジューラーを停止しました")
        
    def _show_next_runs(self):
        """次回実行時刻を表示"""
        jobs = self.scheduler.get_jobs()
        logger.info("=== 次回実行予定 ===")
        for job in jobs:
            next_run = job.next_run_time
            if next_run:
                logger.info(f"{job.name}: {next_run.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                
    async def run_once(self):
        """1回だけ実行（テスト用）"""
        logger.info("テスト実行を開始")
        await self._run_analysis()
        
    def list_jobs(self):
        """設定されているジョブを一覧表示"""
        jobs = self.scheduler.get_jobs()
        for job in jobs:
            logger.info(f"Job ID: {job.id}, Name: {job.name}, Next run: {job.next_run_time}")

async def main():
    """スケジューラーのメインループ"""
    scheduler = FXAnalysisScheduler()
    
    # コマンドライン引数で動作を切り替え
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--once":
        # 1回だけ実行
        await scheduler.run_once()
    else:
        # 定時実行
        scheduler.start()
        
        try:
            # 永続的に実行
            while True:
                await asyncio.sleep(60)  # 1分ごとにチェック
                
                # 現在時刻を表示（生存確認）
                current_time = datetime.now(scheduler.timezone)
                if current_time.minute == 0:  # 毎時0分に状態を表示
                    logger.info(f"スケジューラー稼働中: {current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    scheduler._show_next_runs()
                    
        except KeyboardInterrupt:
            logger.info("キーボード割り込みを検出")
        finally:
            scheduler.stop()

if __name__ == "__main__":
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/scheduler.log'),
            logging.StreamHandler()
        ]
    )
    
    # 実行
    asyncio.run(main())