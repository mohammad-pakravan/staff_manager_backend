"""
Management command برای پاک کردن فایل‌های استوری‌های منقضی شده
فقط فایل‌ها از هارد دیسک پاک می‌شوند و record در دیتابیس باقی می‌ماند
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from apps.hr.models import Story
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'پاک کردن فایل‌های استوری‌های منقضی شده'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='نمایش استوری‌هایی که پاک می‌شوند بدون انجام عملیات',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        # پیدا کردن استوری‌های منقضی شده که هنوز فایل دارند
        expired_stories = Story.objects.filter(
            expiry_date__lte=timezone.now()
        ).exclude(
            # فقط استوری‌هایی که هنوز فایل دارند
            Q(thumbnail_image__isnull=True) & Q(content_file__isnull=True)
        )
        
        count = expired_stories.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('هیچ استوری منقضی شده‌ای با فایل پیدا نشد')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'{count} استوری منقضی شده پیدا شد که فایل‌هایشان پاک می‌شود:')
            )
            for story in expired_stories:
                files = []
                if story.thumbnail_image:
                    files.append(f'thumbnail: {story.thumbnail_image.name}')
                if story.content_file:
                    files.append(f'content: {story.content_file.name}')
                self.stdout.write(f'  - Story ID {story.id}: {", ".join(files)}')
            return
        
        # پاک کردن فایل‌ها
        success_count = 0
        error_count = 0
        
        for story in expired_stories:
            try:
                story.delete_files()  # پاک کردن فایل‌ها و خالی کردن فیلدها
                success_count += 1
                logger.info(f"Files deleted for story {story.id}")
            except Exception as e:
                error_count += 1
                logger.error(f"Error deleting files for story {story.id}: {e}")
                self.stdout.write(
                    self.style.ERROR(f'خطا در پاک کردن فایل‌های استوری {story.id}: {e}')
                )
        
        # نمایش نتیجه
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'{success_count} استوری منقضی شده - فایل‌ها پاک شدند'
                )
            )
        
        if error_count > 0:
            self.stdout.write(
                self.style.ERROR(
                    f'{error_count} خطا در پاک کردن فایل‌ها'
                )
            )

