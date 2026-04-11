import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft } from 'lucide-react';
import { useProduct, useCreateProduct, useUpdateProduct } from '../hooks/useProducts';
import { useCategories } from '../hooks/useCategories';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';

const schema = z.object({
  name: z.string().min(1, 'Name is required'),
  sku: z.string().min(1, 'SKU is required'),
  barcode: z.string().optional(),
  category_id: z.string().optional(),
  description: z.string().optional(),
  unit_price: z.number({ invalid_type_error: 'Enter a valid price' }).min(0),
  cost_price: z.number({ invalid_type_error: 'Enter a valid price' }).min(0),
  tax_rate: z.number().min(0).max(100),
  stock_quantity: z.number().int().min(0),
  min_stock_level: z.number().int().min(0),
  unit_of_measure: z.string().default('pcs'),
  is_active: z.boolean().default(true),
});

type ProductSchemaValues = z.infer<typeof schema>;

export function ProductFormPage() {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEdit = !!id;

  const { data: existing, isLoading: loadingExisting } = useProduct(id ?? '');
  const { data: categories } = useCategories();
  const createProduct = useCreateProduct();
  const updateProduct = useUpdateProduct();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ProductSchemaValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      name: '',
      sku: '',
      barcode: '',
      category_id: '',
      description: '',
      unit_price: 0,
      cost_price: 0,
      tax_rate: 0,
      stock_quantity: 0,
      min_stock_level: 0,
      unit_of_measure: 'pcs',
      is_active: true,
    },
  });

  // When editing and product loads, reset form with existing values
  useEffect(() => {
    if (isEdit && existing) {
      reset({
        name: existing.name,
        sku: existing.sku,
        barcode: existing.barcode ?? '',
        category_id: existing.category_id ?? '',
        description: existing.description ?? '',
        unit_price: existing.unit_price / 100,
        cost_price: existing.cost_price / 100,
        tax_rate: existing.tax_rate,
        stock_quantity: existing.stock_quantity,
        min_stock_level: existing.min_stock_level,
        unit_of_measure: existing.unit_of_measure,
        is_active: existing.is_active,
      });
    }
  }, [isEdit, existing, reset]);

  if (isEdit && loadingExisting) return <LoadingSkeleton />;

  const isPending = createProduct.isPending || updateProduct.isPending;
  const mutationError = createProduct.error || updateProduct.error;

  const onSubmit = (values: ProductSchemaValues) => {
    const payload = {
      name: values.name,
      sku: values.sku,
      barcode: values.barcode || undefined,
      category_id: values.category_id || undefined,
      description: values.description ?? '',
      unit_price: Math.round(values.unit_price * 100),
      cost_price: Math.round(values.cost_price * 100),
      tax_rate: values.tax_rate,
      stock_quantity: values.stock_quantity,
      min_stock_level: values.min_stock_level,
      unit_of_measure: values.unit_of_measure,
      image_url: undefined,
      is_active: values.is_active,
    };

    if (isEdit) {
      updateProduct.mutate(
        { id: id!, data: payload },
        { onSuccess: () => navigate('/products') },
      );
    } else {
      createProduct.mutate(payload, {
        onSuccess: () => navigate('/products'),
      });
    }
  };

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => navigate('/products')}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={16} />
        Products
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">
        {isEdit ? 'Edit Product' : 'New Product'}
      </h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5 max-w-2xl" noValidate>
        {/* Name */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            {...register('name')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.name && (
            <p className="mt-1 text-xs text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* SKU */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            SKU <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            {...register('sku')}
            disabled={isEdit}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
          />
          {errors.sku && (
            <p className="mt-1 text-xs text-red-600">{errors.sku.message}</p>
          )}
        </div>

        {/* Barcode */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Barcode</label>
          <input
            type="text"
            {...register('barcode')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Category */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
          <select
            {...register('category_id')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">None</option>
            {(categories ?? []).map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        {/* Description */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
          <textarea
            {...register('description')}
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Prices row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Unit Price ৳</label>
            <input
              type="number"
              step="0.01"
              min="0"
              {...register('unit_price', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.unit_price && (
              <p className="mt-1 text-xs text-red-600">{errors.unit_price.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cost Price ৳</label>
            <input
              type="number"
              step="0.01"
              min="0"
              {...register('cost_price', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.cost_price && (
              <p className="mt-1 text-xs text-red-600">{errors.cost_price.message}</p>
            )}
          </div>
        </div>

        {/* Tax Rate */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Tax Rate %</label>
          <input
            type="number"
            step="0.01"
            min="0"
            max="100"
            {...register('tax_rate', { valueAsNumber: true })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          {errors.tax_rate && (
            <p className="mt-1 text-xs text-red-600">{errors.tax_rate.message}</p>
          )}
        </div>

        {/* Stock row */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stock Quantity</label>
            <input
              type="number"
              min="0"
              {...register('stock_quantity', { valueAsNumber: true })}
              disabled={isEdit}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-500"
            />
            {isEdit && (
              <p className="mt-1 text-xs text-gray-500">Managed via inventory module</p>
            )}
            {errors.stock_quantity && (
              <p className="mt-1 text-xs text-red-600">{errors.stock_quantity.message}</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Min Stock Level
            </label>
            <input
              type="number"
              min="0"
              {...register('min_stock_level', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.min_stock_level && (
              <p className="mt-1 text-xs text-red-600">{errors.min_stock_level.message}</p>
            )}
          </div>
        </div>

        {/* Unit of Measure */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">Unit of Measure</label>
          <input
            type="text"
            {...register('unit_of_measure')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Is Active */}
        <div className="flex items-center gap-3">
          <input
            id="is_active"
            type="checkbox"
            {...register('is_active')}
            className="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          />
          <label htmlFor="is_active" className="text-sm font-medium text-gray-700">
            Active
          </label>
        </div>

        {/* Server error */}
        {mutationError && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-sm text-red-700">{mutationError.message}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={isPending}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isPending ? 'Saving...' : isEdit ? 'Save Changes' : 'Create Product'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/products')}
            className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
