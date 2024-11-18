from .services import AcademicYearTransitionService
from .models import AcademicYearTransition
from celery import shared_task

import logging

logger = logging.getLogger(__name__)

@shared_task
def process_academic_year_transition(transition_id):
    """Process academic year transition asynchronously"""
    transition = AcademicYearTransition.objects.get(id=transition_id)
    
    service = AcademicYearTransitionService(
        from_year=transition.from_year,
        to_year=transition.to_year,
        user=transition.processed_by
    )

    try:
        service.process_transition()
    except Exception as e:
        # Log error and send notification
        logger.error(f"Academic year transition failed: {str(e)}")
        # Notify relevant personnel