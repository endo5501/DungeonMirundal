"""新施設システムパッケージ"""

from .core.facility_service import FacilityService, MenuItem
from .core.service_result import ServiceResult
from .core.facility_controller import FacilityController
from .core.facility_registry import FacilityRegistry, facility_registry

__all__ = [
    'FacilityService',
    'MenuItem',
    'ServiceResult',
    'FacilityController',
    'FacilityRegistry',
    'facility_registry',
]