# core/views/monitoring.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import psutil
import os


class HealthCheckView(APIView):
    permission_classes = []
    authentication_classes = []

    def get(self, request):
        health_status = {"status": "healthy", "components": {}}

        try:
            # Database check
            self._check_database(health_status)

            # Cache check
            self._check_cache(health_status)

            # System resources check
            self._check_system_resources(health_status)

            # Storage check
            self._check_storage(health_status)

            # Overall status
            if any(
                comp.get("status") == "unhealthy"
                for comp in health_status["components"].values()
            ):
                health_status["status"] = "unhealthy"

            return Response(health_status)

        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            return Response(health_status, status=503)

    def _check_database(self, health_status):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            health_status["components"]["database"] = {
                "status": "healthy",
                "message": "Connected successfully",
            }
        except Exception as e:
            health_status["components"]["database"] = {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_cache(self, health_status):
        try:
            cache.set("health_check", "ok", 1)
            result = cache.get("health_check")
            if result != "ok":
                raise ValueError("Cache test failed")
            health_status["components"]["cache"] = {
                "status": "healthy",
                "message": "Working properly",
            }
        except Exception as e:
            health_status["components"]["cache"] = {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_system_resources(self, health_status):
        try:
            memory = psutil.virtual_memory()
            cpu_usage = psutil.cpu_percent(interval=1)

            # Define thresholds
            memory_threshold = 90  # 90% memory usage
            cpu_threshold = 90  # 90% CPU usage

            memory_status = {
                "total": self._format_bytes(memory.total),
                "available": self._format_bytes(memory.available),
                "percent_used": memory.percent,
                "status": "healthy" if memory.percent < memory_threshold else "warning",
            }

            cpu_status = {
                "percent_used": cpu_usage,
                "status": "healthy" if cpu_usage < cpu_threshold else "warning",
            }

            health_status["components"]["system"] = {
                "status": "healthy"
                if (
                    memory_status["status"] == "healthy"
                    and cpu_status["status"] == "healthy"
                )
                else "warning",
                "memory": memory_status,
                "cpu": cpu_status,
            }
        except Exception as e:
            health_status["components"]["system"] = {
                "status": "unhealthy",
                "error": str(e),
            }

    def _check_storage(self, health_status):
        try:
            storage_threshold = 90  # 90% storage usage
            storage_info = {}

            # Check media storage
            if hasattr(settings, "MEDIA_ROOT"):
                media_usage = self._get_directory_usage(settings.MEDIA_ROOT)
                storage_info["media"] = {
                    "path": settings.MEDIA_ROOT,
                    "total": self._format_bytes(media_usage["total"]),
                    "used": self._format_bytes(media_usage["used"]),
                    "percent_used": media_usage["percent"],
                    "status": "healthy"
                    if media_usage["percent"] < storage_threshold
                    else "warning",
                }

            # Check static storage
            if hasattr(settings, "STATIC_ROOT"):
                static_usage = self._get_directory_usage(settings.STATIC_ROOT)
                storage_info["static"] = {
                    "path": settings.STATIC_ROOT,
                    "total": self._format_bytes(static_usage["total"]),
                    "used": self._format_bytes(static_usage["used"]),
                    "percent_used": static_usage["percent"],
                    "status": "healthy"
                    if static_usage["percent"] < storage_threshold
                    else "warning",
                }

            health_status["components"]["storage"] = {
                "status": "healthy"
                if all(info["status"] == "healthy" for info in storage_info.values())
                else "warning",
                "details": storage_info,
            }
        except Exception as e:
            health_status["components"]["storage"] = {
                "status": "unhealthy",
                "error": str(e),
            }

    def _get_directory_usage(self, path):
        if not os.path.exists(path):
            return {"total": 0, "used": 0, "percent": 0}

        usage = psutil.disk_usage(path)
        return {"total": usage.total, "used": usage.used, "percent": usage.percent}

    def _format_bytes(self, bytes):
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if bytes < 1024:
                return f"{bytes:.2f}{unit}"
            bytes /= 1024
