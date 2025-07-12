"""
画像をクラウドストレージにアップロードするモジュール
"""
import os
import logging
from pathlib import Path
from typing import Optional
import requests
import base64

logger = logging.getLogger(__name__)

class ImageUploader:
    """画像アップロード用の基底クラス"""
    
    def upload(self, image_path: Path) -> Optional[str]:
        """画像をアップロードしてURLを返す"""
        raise NotImplementedError

class ImgurUploader(ImageUploader):
    """Imgurを使用した画像アップロード"""
    
    def __init__(self):
        self.client_id = os.getenv("IMGUR_CLIENT_ID")
        if not self.client_id:
            raise ValueError("IMGUR_CLIENT_IDが設定されていません")
            
    def upload(self, image_path: Path) -> Optional[str]:
        """画像をImgurにアップロード"""
        try:
            with open(image_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode()
                
            headers = {"Authorization": f"Client-ID {self.client_id}"}
            data = {"image": image_data, "type": "base64"}
            
            response = requests.post(
                "https://api.imgur.com/3/image",
                headers=headers,
                data=data
            )
            
            if response.status_code == 200:
                result = response.json()
                image_url = result["data"]["link"]
                logger.info(f"画像をアップロードしました: {image_url}")
                return image_url
            else:
                logger.error(f"アップロードエラー: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Imgurアップロードエラー: {e}")
            return None

class CloudinaryUploader(ImageUploader):
    """Cloudinaryを使用した画像アップロード"""
    
    def __init__(self):
        try:
            import cloudinary
            import cloudinary.uploader
            
            cloudinary.config(
                cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
                api_key=os.getenv("CLOUDINARY_API_KEY"),
                api_secret=os.getenv("CLOUDINARY_API_SECRET")
            )
            self.cloudinary = cloudinary
        except ImportError:
            logger.warning("cloudinaryパッケージがインストールされていません")
            self.cloudinary = None
            
    def upload(self, image_path: Path) -> Optional[str]:
        """画像をCloudinaryにアップロード"""
        if not self.cloudinary:
            return None
            
        try:
            result = self.cloudinary.uploader.upload(
                str(image_path),
                folder="fx_charts",
                resource_type="image"
            )
            
            image_url = result["secure_url"]
            logger.info(f"画像をアップロードしました: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"Cloudinaryアップロードエラー: {e}")
            return None

class S3Uploader(ImageUploader):
    """AWS S3を使用した画像アップロード"""
    
    def __init__(self):
        try:
            import boto3
            
            # ECS環境ではIAMロールで認証
            self.s3_client = boto3.client('s3')
            # Lambda環境ではS3_BUCKET_NAMEを優先
            self.bucket_name = os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_S3_BUCKET")
            self.region = os.getenv("AWS_REGION", "ap-northeast-1")
        except ImportError:
            logger.warning("boto3パッケージがインストールされていません")
            self.s3_client = None
            
    def upload(self, image_path: Path) -> Optional[str]:
        """画像をS3にアップロードして署名付きURLを返す"""
        if not self.s3_client or not self.bucket_name:
            logger.warning(f"S3設定が不完全です: bucket={self.bucket_name}, client={self.s3_client is not None}")
            return None
            
        try:
            import datetime
            
            # タイムスタンプ付きキーを生成
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            key = f"fx_charts/{timestamp}_{image_path.name}"
            
            # ファイルをS3にアップロード
            self.s3_client.upload_file(
                str(image_path),
                self.bucket_name,
                key,
                ExtraArgs={
                    'ContentType': 'image/png',
                    'ACL': 'bucket-owner-full-control'  # プライベートアップロード
                }
            )
            
            # 署名付きURLを生成（7日間有効）
            presigned_url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': key},
                ExpiresIn=604800  # 7日間
            )
            
            logger.info(f"画像をS3にアップロードしました: {key}")
            return presigned_url
            
        except Exception as e:
            logger.error(f"S3アップロードエラー: {e}")
            return None

def get_uploader() -> ImageUploader:
    """設定に基づいて適切なアップローダーを返す"""
    
    # Lambda環境ではS3_BUCKET_NAMEを優先
    s3_bucket = os.getenv("S3_BUCKET_NAME") or os.getenv("AWS_S3_BUCKET")
    cloudinary_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    imgur_id = os.getenv("IMGUR_CLIENT_ID")
    
    logger.info(f"アップローダー設定確認: S3={bool(s3_bucket)}, Cloudinary={bool(cloudinary_name)}, Imgur={bool(imgur_id)}")
    
    # 優先順位: S3 > Cloudinary > Imgur (ECS環境ではS3を優先)
    if s3_bucket:
        logger.info(f"S3Uploaderを使用します: bucket={s3_bucket}")
        try:
            return S3Uploader()
        except Exception as e:
            logger.error(f"S3Uploader初期化エラー: {e}")
            return None
    elif cloudinary_name:
        logger.info("CloudinaryUploaderを使用します")
        return CloudinaryUploader()
    elif imgur_id:
        logger.info("ImgurUploaderを使用します")
        return ImgurUploader()
    else:
        logger.warning("画像アップロード設定がありません")
        return None