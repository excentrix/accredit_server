# core/management/commands/backup_data.py
from django.core.management.base import BaseCommand
from django.conf import settings
from django.utils import timezone
from django.core import serializers
from core.models import *
from azure.storage.blob import BlobServiceClient
import os
import json
import shutil
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Backup system data and files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--upload-to-azure',
            action='store_true',
            help='Upload backup to Azure Blob Storage',
        )

    def handle(self, *args, **options):
        try:
            backup_dir = self._create_backup_directory()
            
            # Backup data
            self._backup_data(backup_dir)
            
            # Backup media files
            self._backup_media_files(backup_dir)
            
            # Create archive
            archive_path = self._create_archive(backup_dir)
            
            # Upload to Azure if specified
            if options['upload_to-azure']:
                self._upload_to_azure(archive_path)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            self.stdout.write(
                self.style.SUCCESS('Successfully created backup')
            )
            
        except Exception as e:
            logger.error(f"Backup failed: {str(e)}")
            self.stdout.write(
                self.style.ERROR(f'Backup failed: {str(e)}')
            )

    def _create_backup_directory(self):
        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BACKUP_DIR, f'backup_{timestamp}')
        os.makedirs(backup_dir, exist_ok=True)
        return backup_dir

    def _backup_data(self, backup_dir):
        models_to_backup = [
            Template, DataSubmission, SubmissionData, 
            CustomUser, Department, Role, Permission
        ]
        
        for model in models_to_backup:
            data = serializers.serialize('json', model.objects.all())
            filename = f"{model._meta.model_name}.json"
            with open(os.path.join(backup_dir, filename), 'w') as f:
                f.write(data)

    def _backup_media_files(self, backup_dir):
        if hasattr(settings, 'MEDIA_ROOT') and os.path.exists(settings.MEDIA_ROOT):
            media_backup_dir = os.path.join(backup_dir, 'media')
            shutil.copytree(settings.MEDIA_ROOT, media_backup_dir)

    def _create_archive(self, backup_dir):
        archive_name = f"{os.path.basename(backup_dir)}.tar.gz"
        archive_path = os.path.join(settings.BACKUP_DIR, archive_name)
        shutil.make_archive(
            archive_path.rsplit('.', 1)[0],
            'gztar',
            backup_dir
        )
        # Remove the uncompressed backup directory
        shutil.rmtree(backup_dir)
        return archive_path

    def _upload_to_azure(self, archive_path):
        try:
            # Get Azure storage connection string from settings
            connect_str = settings.AZURE_STORAGE_CONNECTION_STRING
            
            # Create the BlobServiceClient
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            
            # Get container client
            container_name = settings.AZURE_BACKUP_CONTAINER
            container_client = blob_service_client.get_container_client(container_name)
            
            # Generate blob name (you can modify this naming convention)
            blob_name = f"backups/{os.path.basename(archive_path)}"
            
            # Get blob client
            blob_client = container_client.get_blob_client(blob_name)
            
            # Upload the file
            with open(archive_path, "rb") as data:
                blob_client.upload_blob(data, overwrite=True)
                
            logger.info(f"Successfully uploaded backup to Azure: {blob_name}")
            
        except Exception as e:
            logger.error(f"Failed to upload backup to Azure: {str(e)}")
            raise

    def _cleanup_old_backups(self):
        # Local cleanup
        retention_days = getattr(settings, 'BACKUP_RETENTION_DAYS', 30)
        cutoff_date = timezone.now() - timezone.timedelta(days=retention_days)
        
        # Clean local backups
        for filename in os.listdir(settings.BACKUP_DIR):
            if not filename.endswith('.tar.gz'):
                continue
                
            file_path = os.path.join(settings.BACKUP_DIR, filename)
            file_time = timezone.datetime.fromtimestamp(
                os.path.getctime(file_path)
            )
            
            if file_time < cutoff_date:
                os.remove(file_path)

        # Clean Azure backups
        try:
            connect_str = settings.AZURE_STORAGE_CONNECTION_STRING
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
            container_client = blob_service_client.get_container_client(
                settings.AZURE_BACKUP_CONTAINER
            )

            # List all blobs and delete old ones
            blobs = container_client.list_blobs(name_starts_with="backups/")
            for blob in blobs:
                # Azure stores timestamps in UTC
                blob_date = blob.last_modified.replace(tzinfo=timezone.utc)
                if blob_date < cutoff_date:
                    container_client.delete_blob(blob.name)
                    logger.info(f"Deleted old backup from Azure: {blob.name}")

        except Exception as e:
            logger.error(f"Failed to cleanup Azure backups: {str(e)}")