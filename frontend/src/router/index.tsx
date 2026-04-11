import { Routes, Route } from 'react-router-dom';
import { AuthLayout } from '../components/layout/AuthLayout';
import { AppLayout } from '../components/layout/AppLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { LoginPage } from '../pages/LoginPage';
import { DashboardPage } from '../pages/DashboardPage';
import { CategoriesPage } from '../pages/CategoriesPage';
import { ProductsPage } from '../pages/ProductsPage';
import { ProductDetailPage } from '../pages/ProductDetailPage';
import { ProductFormPage } from '../pages/ProductFormPage';
import { ProductImportPage } from '../pages/ProductImportPage';
import { InventoryMovementsPage } from '../pages/InventoryMovementsPage';
import { InventoryValuationPage } from '../pages/InventoryValuationPage';
import { SuppliersPage } from '../pages/SuppliersPage';
import { PurchaseOrdersPage } from '../pages/PurchaseOrdersPage';
import { PurchaseOrderFormPage } from '../pages/PurchaseOrderFormPage';
import { PurchaseOrderDetailPage } from '../pages/PurchaseOrderDetailPage';
import { PromotionsPage } from '../pages/PromotionsPage';

export function AppRoutes() {
  return (
    <Routes>
      {/* Public routes */}
      <Route
        path="/login"
        element={
          <AuthLayout>
            <LoginPage />
          </AuthLayout>
        }
      />

      {/* Protected routes */}
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="categories" element={<CategoriesPage />} />
          <Route path="products" element={<ProductsPage />} />
          <Route path="products/new" element={<ProductFormPage />} />
          <Route path="products/import" element={<ProductImportPage />} />
          <Route path="products/:id" element={<ProductDetailPage />} />
          <Route path="products/:id/edit" element={<ProductFormPage />} />
          <Route path="inventory/movements" element={<InventoryMovementsPage />} />
          <Route path="inventory/valuation" element={<InventoryValuationPage />} />
          <Route path="suppliers" element={<SuppliersPage />} />
          <Route path="purchases" element={<PurchaseOrdersPage />} />
          <Route path="purchases/new" element={<PurchaseOrderFormPage />} />
          <Route path="purchases/:id" element={<PurchaseOrderDetailPage />} />
          <Route path="promotions" element={<PromotionsPage />} />
        </Route>
      </Route>
    </Routes>
  );
}
