import { useState } from 'react';
import { Outlet, NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Package,
  Warehouse,
  Truck,
  ShoppingCart,
  Tag,
  Receipt,
  Calculator,
  BarChart3,
  Menu,
  X,
  LogOut,
  type LucideIcon,
} from 'lucide-react';
import { useCurrentUser, useLogout } from '../../hooks/useAuth';

interface NavItem {
  label: string;
  icon: LucideIcon;
  to: string;
  enabled: boolean;
}

const NAV_ITEMS: NavItem[] = [
  { label: 'Dashboard', icon: LayoutDashboard, to: '/', enabled: true },
  { label: 'Products', icon: Package, to: '/products', enabled: true },
  { label: 'Categories', icon: Tag, to: '/categories', enabled: true },
  { label: 'Inventory', icon: Warehouse, to: '/inventory/movements', enabled: true },
  { label: 'Suppliers', icon: Truck, to: '/suppliers', enabled: true },
  { label: 'Purchases', icon: ShoppingCart, to: '/purchases', enabled: true },
  { label: 'Promotions', icon: Receipt, to: '/promotions', enabled: true },
  { label: 'Sales', icon: Calculator, to: '/sales', enabled: true },
  { label: 'Accounting', icon: BarChart3, to: '/accounting/accounts', enabled: true },
  { label: 'Reports', icon: BarChart3, to: '/reports', enabled: false },
];

const ROLE_BADGE_COLORS: Record<string, string> = {
  admin: 'bg-red-100 text-red-700',
  manager: 'bg-blue-100 text-blue-700',
  staff: 'bg-green-100 text-green-700',
};

export function AppLayout() {
  const [expanded, setExpanded] = useState(true);
  const { data: user } = useCurrentUser();
  const logout = useLogout();

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <aside
        className={`flex flex-col bg-white shadow-sm transition-all duration-200 ${
          expanded ? 'w-64' : 'w-16'
        }`}
      >
        {/* Sidebar header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-100">
          {expanded && (
            <span className="text-lg font-bold text-blue-600">ShopERP</span>
          )}
          <button
            onClick={() => setExpanded((v) => !v)}
            className="p-1.5 rounded-md hover:bg-gray-100 text-gray-500"
            aria-label="Toggle sidebar"
          >
            {expanded ? <X size={18} /> : <Menu size={18} />}
          </button>
        </div>

        {/* Nav items */}
        <nav className="flex-1 py-4 space-y-1 px-2">
          {NAV_ITEMS.map(({ label, icon: Icon, to, enabled }) =>
            enabled ? (
              <NavLink
                key={label}
                to={to}
                end={to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium ${
                    isActive
                      ? 'bg-blue-50 text-blue-700'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`
                }
              >
                <Icon size={18} className="flex-shrink-0" />
                {expanded && <span>{label}</span>}
              </NavLink>
            ) : (
              <span
                key={label}
                className="flex items-center gap-3 px-3 py-2 rounded-md text-sm font-medium cursor-not-allowed select-none text-gray-400"
              >
                <Icon size={18} className="flex-shrink-0" />
                {expanded && <span>{label}</span>}
              </span>
            ),
          )}
        </nav>
      </aside>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="bg-white shadow-sm px-6 py-3 flex items-center justify-between">
          <span className="text-lg font-bold text-blue-600">ShopERP</span>
          {user && (
            <div className="flex items-center gap-3">
              <span className="text-sm text-gray-700 font-medium">
                {user.name}
              </span>
              <span
                className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                  ROLE_BADGE_COLORS[user.role] ?? 'bg-gray-100 text-gray-600'
                }`}
              >
                {user.role}
              </span>
              <button
                onClick={() => logout.mutate()}
                disabled={logout.isPending}
                className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-gray-800 px-2 py-1 rounded-md hover:bg-gray-100"
              >
                <LogOut size={15} />
                <span>Sign out</span>
              </button>
            </div>
          )}
        </header>

        {/* Page content */}
        <main className="flex-1 p-6 overflow-auto">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
