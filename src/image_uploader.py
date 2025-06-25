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
            
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
                aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
            )
            self.bucket_name = os.getenv("AWS_S3_BUCKET")
            self.region = os.getenv("AWS_REGION", "ap-northeast-1")
        except ImportError:
            logger.warning("boto3パッケージがインストールされていません")
            self.s3_client = None
            
    def upload(self, image_path: Path) -> Optional[str]:
        """画像をS3にアップロード"""
        if not self.s3_client or not self.bucket_name:
            return None
            
        try:
            key = f"fx_charts/{image_path.name}"
            
            self.s3_client.upload_file(
                str(image_path),
                self.bucket_name,
                key,
                ExtraArgs={'ContentType': 'image/png'}
            )
            
            image_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{key}"
            logger.info(f"画像をアップロードしました: {image_url}")
            return image_url
            
        except Exception as e:
            logger.error(f"S3アップロードエラー: {e}")
            return None

def get_uploader() -> ImageUploader:
    """設定に基づいて適切なアップローダーを返す"""
    
    # 優先順位: Cloudinary > Imgur > S3
    if os.getenv("CLOUDINARY_CLOUD_NAME"):
        return CloudinaryUploader()
    elif os.getenv("IMGUR_CLIENT_ID"):
        return ImgurUploader()
    elif os.getenv("AWS_S3_BUCKET"):
        return S3Uploader()
    else:
        logger.warning("画像アップロード設定がありません")
        return None