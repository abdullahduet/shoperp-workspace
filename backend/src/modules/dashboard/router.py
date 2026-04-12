from fastapi import APIRouter, Depends
from src.core.auth import require_roles
from src.modules.dashboard import controller

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

router.add_api_route("/summary", controller.get_summary, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/trends", controller.get_trends, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
