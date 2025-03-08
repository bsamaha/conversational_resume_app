import contextlib
import json
import logging
import boto3
from datetime import datetime
from app.core.config import settings
from app.schemas.query import UserInfo
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self):
        # Use default credential chain to support all credential types
        # This will automatically use credentials from environment variables, EC2 instance profiles,
        # or AWS credentials file in that order of preference
        self.s3_client = boto3.client(
            's3',
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.AWS_S3_BUCKET_NAME
        
        # Log initialization
        logger.info(f"Initialized S3Service with region {settings.AWS_REGION} and bucket {self.bucket_name}")

    async def save_chat_log(self, session_id: str, user_info: UserInfo, messages: List[Dict[str, Any]]):
        """
        Save a complete chat log to S3 using a data lake compatible structure
        
        Args:
            session_id: Unique identifier for the chat session
            user_info: User information from the form
            messages: List of chat messages
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Get current timestamp for partitioning
            now = datetime.now()
            year = now.strftime("%Y")
            month = now.strftime("%m")
            day = now.strftime("%d")
            timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

            # Format the chat data for storage
            chat_data = {
                "metadata": {
                    "session_id": session_id,
                    "timestamp": timestamp,
                    "user_info": {
                        "name": user_info.name,
                        "email": user_info.email,
                        "company_name": user_info.companyName,
                        "company_type": user_info.companyType,
                        "purpose": user_info.purpose,
                        "job_role": user_info.jobRole,
                    },
                },
                "messages": [
                    {
                        "content": message["content"],
                        "is_user": message["is_user"],
                        "timestamp": (
                            message["timestamp"].isoformat()
                            if isinstance(message["timestamp"], datetime)
                            else message["timestamp"]
                        ),
                    }
                    for message in messages
                ],
                "analytics": {
                    "message_count": len(messages),
                    "user_message_count": sum(
                        bool(msg.get("is_user", False)) for msg in messages
                    ),
                    "assistant_message_count": sum(
                        not msg.get("is_user", False) for msg in messages
                    ),
                    "conversation_duration_minutes": self._calculate_conversation_duration(
                        messages
                    ),
                },
            }

            # Create a data lake compatible key structure with Hive-style partitioning
            # This structure works well with AWS Athena, Glue, and other analytics services
            # Include company type for organizational analytics
            key = f"chats/year={year}/month={month}/day={day}/company_type={user_info.companyType}/purpose={user_info.purpose}/job_role={user_info.jobRole}/{session_id}.json"

            # Convert to JSON and upload to S3
            chat_json = json.dumps(chat_data)
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=chat_json,
                ContentType='application/json'
            )

            logger.info(f"Successfully saved chat log to S3: {key}")
            return True

        except Exception as e:
            logger.error(f"Error saving chat log to S3: {str(e)}")
            return False
    
    def _calculate_conversation_duration(self, messages: List[Dict[str, Any]]) -> float:
        """Calculate the approximate duration of the conversation in minutes"""
        if len(messages) < 2:
            return 0

        with contextlib.suppress(ValueError, TypeError, AttributeError):
            # Get first and last message timestamps
            first_time = messages[0].get("timestamp")
            last_time = messages[-1].get("timestamp")

            # Convert to datetime if they're strings
            if isinstance(first_time, str):
                first_time = datetime.fromisoformat(first_time.replace('Z', '+00:00'))
            if isinstance(last_time, str):
                last_time = datetime.fromisoformat(last_time.replace('Z', '+00:00'))

            # Calculate duration in minutes
            if isinstance(first_time, datetime) and isinstance(last_time, datetime):
                delta = last_time - first_time
                return delta.total_seconds() / 60
        return 0 