import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray, useWatch, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, ArrowLeft } from 'lucide-react';
import { useCreatePO } from '../hooks/usePurchaseOrders';
import { useSuppliers } from '../hooks/useSuppliers';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ProductSearchSelect } from '../components/ui/ProductSearchSelect';

const itemSchema = z.object({
  product_id: z.string().min(1, 'Select a product'),
  quantity: z
    .number({ invalid_type_error: 'Enter a valid quantity' })
    .int()
    .min(1, 'Must be at least 1'),
  unit_cost: z
    .number({ invalid_type_error: 'Enter a valid cost' })
    .min(0, 'Must be 0 or more'),
});

const poSchema = z.object({
  supplier_id: z.string().min(1, 'Select a supplier'),
  expected_date: z.string().optional().default(''),
  notes: z.string().optional().default(''),
  items: z.array(itemSchema).min(1, 'At least one item is required'),
});

type POSchemaValues = z.infer<typeof poSchema>;

export function PurchaseOrderFormPage() {
  const navigate = useNavigate();
  const createPO = useCreatePO();

  const { data: suppliersData, isLoading: loadingSuppliers } = useSuppliers({
    is_active: true,
    limit: 100,
  });

  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<POSchemaValues>({
    resolver: zodResolver(poSchema),
    defaultValues: {
      supplier_id: '',
      expected_date: '',
      notes: '',
      items: [{ product_id: '', quantity: 1, unit_cost: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'items' });

  const watchedItems = useWatch({ control, name: 'items' });

  const subtotalPaisa = (watchedItems ?? []).reduce((sum, item) => {
    const qty = typeof item.quantity === 'number' ? item.quantity : 0;
    const costPaisa = Math.round((typeof item.unit_cost === 'number' ? item.unit_cost : 0) * 100);
    return sum + qty * costPaisa;
  }, 0);

  const onSubmit = (values: POSchemaValues) => {
    const payload = {
      supplier_id: values.supplier_id,
      expected_date: values.expected_date || undefined,
      notes: values.notes || undefined,
      items: values.items.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_cost: Math.round(item.unit_cost * 100),
      })),
    };

    createPO.mutate(payload, {
      onSuccess: (po) => navigate(`/purchases/${po.id}`),
    });
  };

  if (loadingSuppliers) return <LoadingSkeleton />;

  const suppliers = suppliersData?.data ?? [];

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => navigate('/purchases')}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={16} />
        Purchase Orders
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">New Purchase Order</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-4xl" noValidate>
        {/* Supplier */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Supplier <span className="text-red-500">*</span>
          </label>
          <select
            {...register('supplier_id')}
            className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">Select supplier...</option>
            {suppliers.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
          {errors.supplier_id && (
            <p className="mt-1 text-xs text-red-600">{errors.supplier_id.message}</p>
          )}
        </div>

        {/* Expected Date + Notes */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Expected Date</label>
            <input
              type="date"
              {...register('expected_date')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
            <textarea
              {...register('notes')}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Line Items */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-gray-900">Items</h2>
            <button
              type="button"
              onClick={() => append({ product_id: '', quantity: 1, unit_cost: 0 })}
              className="flex items-center gap-1.5 px-3 py-1.5 border border-gray-300 text-sm text-gray-700 rounded-md hover:bg-gray-50"
            >
              <Plus size={15} />
              Add Item
            </button>
          </div>

          {errors.items && !Array.isArray(errors.items) && (
            <p className="mb-2 text-xs text-red-600">{errors.items.message}</p>
          )}

          {/* Column headers */}
          <div className="grid grid-cols-12 gap-2 text-xs font-medium text-gray-500 uppercase mb-2 px-1">
            <span className="col-span-5">Product</span>
            <span className="col-span-2">Qty</span>
            <span className="col-span-3">Unit Cost ৳</span>
            <span className="col-span-1">Line Total</span>
            <span className="col-span-1"></span>
          </div>

          <div className="space-y-2">
            {fields.map((field, index) => {
              const item = watchedItems?.[index];
              const qty = typeof item?.quantity === 'number' ? item.quantity : 0;
              const cost =
                typeof item?.unit_cost === 'number' ? item.unit_cost : 0;
              const lineTotal = qty * cost;

              return (
                <div key={field.id} className="grid grid-cols-12 gap-2 items-start">
                  {/* Product */}
                  <div className="col-span-5">
                    <Controller
                      control={control}
                      name={`items.${index}.product_id`}
                      render={({ field }) => (
                        <ProductSearchSelect
                          value={field.value}
                          onChange={field.onChange}
                          onBlur={field.onBlur}
                          hasError={!!errors.items?.[index]?.product_id}
                        />
                      )}
                    />
                    {errors.items?.[index]?.product_id && (
                      <p className="mt-0.5 text-xs text-red-600">
                        {errors.items[index]?.product_id?.message}
                      </p>
                    )}
                  </div>

                  {/* Quantity */}
                  <div className="col-span-2">
                    <input
                      type="number"
                      min={1}
                      {...register(`items.${index}.quantity`, { valueAsNumber: true })}
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {errors.items?.[index]?.quantity && (
                      <p className="mt-0.5 text-xs text-red-600">
                        {errors.items[index]?.quantity?.message}
                      </p>
                    )}
                  </div>

                  {/* Unit Cost */}
                  <div className="col-span-3">
                    <input
                      type="number"
                      min={0}
                      step="0.01"
                      {...register(`items.${index}.unit_cost`, { valueAsNumber: true })}
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {errors.items?.[index]?.unit_cost && (
                      <p className="mt-0.5 text-xs text-red-600">
                        {errors.items[index]?.unit_cost?.message}
                      </p>
                    )}
                  </div>

                  {/* Line total */}
                  <div className="col-span-1 py-2 font-mono text-sm text-gray-700">
                    ৳{lineTotal.toFixed(2)}
                  </div>

                  {/* Remove button */}
                  <div className="col-span-1 flex justify-center">
                    <button
                      type="button"
                      onClick={() => remove(index)}
                      disabled={fields.length === 1}
                      className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-30 disabled:cursor-not-allowed mt-1"
                      title="Remove item"
                    >
                      <Trash2 size={15} />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Subtotal */}
          <div className="flex justify-end mt-4 pt-4 border-t border-gray-100">
            <div className="text-sm font-semibold text-gray-900">
              Subtotal: <span className="font-mono">৳{(subtotalPaisa / 100).toFixed(2)}</span>
            </div>
          </div>
        </div>

        {/* Server error */}
        {createPO.error && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-sm text-red-700">{createPO.error.message}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={createPO.isPending}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createPO.isPending ? 'Creating...' : 'Create Purchase Order'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/purchases')}
            className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
