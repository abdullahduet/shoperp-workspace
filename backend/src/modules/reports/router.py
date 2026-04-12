from fastapi import APIRouter, Depends
from src.core.auth import get_current_user, require_roles
from src.modules.reports import controller

router = APIRouter(prefix="/reports", tags=["reports"])

router.add_api_route("/sales", controller.get_sales_report, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/profit-loss", controller.get_profit_loss, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/top-products", controller.get_top_products, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/low-stock", controller.get_low_stock, methods=["GET"],
                     dependencies=[Depends(get_current_user)])
router.add_api_route("/purchases", controller.get_purchases_report, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/expenses", controller.get_expenses_report, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
router.add_api_route("/inventory-valuation", controller.get_inventory_valuation, methods=["GET"],
                     dependencies=[Depends(require_roles("admin", "manager"))])
