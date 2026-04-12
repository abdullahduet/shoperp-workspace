import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray, useWatch } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, ArrowLeft } from 'lucide-react';
import type { AxiosError } from 'axios';
import { useRecordSale } from '../hooks/useSales';
import type { SalePayload } from '../types/sale.types';

const itemSchema = z.object({
  product_id: z.string().min(1, 'Product ID required'),
  quantity: z
    .number({ invalid_type_error: 'Enter a valid quantity' })
    .int()
    .min(1, 'Must be at least 1'),
  unit_price: z
    .number({ invalid_type_error: 'Enter a valid price' })
    .min(0, 'Must be 0 or more'),
});

const saleSchema = z.object({
  items: z.array(itemSchema).min(1, 'At least one item required'),
  payment_method: z.enum(['cash', 'card', 'mobile', 'credit']).default('cash'),
  customer_name: z.string().optional().default(''),
  notes: z.string().optional().default(''),
});

type SaleSchemaValues = z.infer<typeof saleSchema>;

export function RecordSalePage() {
  const navigate = useNavigate();
  const recordSale = useRecordSale();

  const {
    register,
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<SaleSchemaValues>({
    resolver: zodResolver(saleSchema),
    defaultValues: {
      items: [{ product_id: '', quantity: 1, unit_price: 0 }],
      payment_method: 'cash',
      customer_name: '',
      notes: '',
    },
  });

  const { fields, append, remove } = useFieldArray({ control, name: 'items' });

  const watchedItems = useWatch({ control, name: 'items' });

  const subtotalDisplay = (watchedItems ?? [])
    .reduce((sum, item) => {
      return (
        sum +
        (typeof item.unit_price === 'number' ? item.unit_price : 0) *
          (typeof item.quantity === 'number' ? item.quantity : 0)
      );
    }, 0)
    .toFixed(2);

  const onSubmit = (values: SaleSchemaValues) => {
    const payload: SalePayload = {
      items: values.items.map((item) => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: Math.round(item.unit_price * 100),
      })),
      payment_method: values.payment_method,
      customer_name: values.customer_name || undefined,
      notes: values.notes || undefined,
    };

    recordSale.mutate(payload, {
      onSuccess: (newSale) => navigate(`/sales/${newSale.id}`),
    });
  };

  const mutationError =
    (recordSale.error as AxiosError<{ error: string }> | null)?.response?.data?.error ||
    (recordSale.error instanceof Error ? recordSale.error.message : null) ||
    (recordSale.error ? 'Failed to record sale' : null);

  return (
    <div>
      {/* Back */}
      <button
        onClick={() => navigate('/sales')}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900 mb-6"
      >
        <ArrowLeft size={16} />
        Back to Sales
      </button>

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Record Sale</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6 max-w-4xl" noValidate>
        {/* Line Items */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <h2 className="text-base font-semibold text-gray-900">Items</h2>
            <button
              type="button"
              onClick={() => append({ product_id: '', quantity: 1, unit_price: 0 })}
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
            <span className="col-span-5">Product ID</span>
            <span className="col-span-2">Qty</span>
            <span className="col-span-3">Unit Price ৳</span>
            <span className="col-span-1">Total</span>
            <span className="col-span-1"></span>
          </div>

          <div className="space-y-2">
            {fields.map((field, index) => {
              const item = watchedItems?.[index];
              const qty = typeof item?.quantity === 'number' ? item.quantity : 0;
              const unitPrice = typeof item?.unit_price === 'number' ? item.unit_price : 0;
              const rowTotal = unitPrice * qty;

              return (
                <div key={field.id} className="grid grid-cols-12 gap-2 items-start">
                  {/* Product ID */}
                  <div className="col-span-5">
                    <input
                      type="text"
                      {...register(`items.${index}.product_id`)}
                      placeholder="Product UUID or SKU"
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
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

                  {/* Unit Price */}
                  <div className="col-span-3">
                    <input
                      type="number"
                      min={0}
                      step="0.01"
                      {...register(`items.${index}.unit_price`, { valueAsNumber: true })}
                      className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {errors.items?.[index]?.unit_price && (
                      <p className="mt-0.5 text-xs text-red-600">
                        {errors.items[index]?.unit_price?.message}
                      </p>
                    )}
                  </div>

                  {/* Row total */}
                  <div className="col-span-1 py-2 font-mono text-sm text-gray-700">
                    ৳{rowTotal.toFixed(2)}
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
              Subtotal:{' '}
              <span className="font-mono">৳{subtotalDisplay}</span>
            </div>
          </div>
        </div>

        {/* Payment Method */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Payment Method
          </label>
          <select
            {...register('payment_method')}
            className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="cash">Cash</option>
            <option value="card">Card</option>
            <option value="mobile">Mobile</option>
            <option value="credit">Credit</option>
          </select>
          {errors.payment_method && (
            <p className="mt-1 text-xs text-red-600">{errors.payment_method.message}</p>
          )}
        </div>

        {/* Customer Name + Notes */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Customer Name <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              {...register('customer_name')}
              placeholder="Walk-in"
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Notes <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              {...register('notes')}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Mutation error */}
        {mutationError && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-sm text-red-700">{mutationError}</p>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3 pt-2">
          <button
            type="submit"
            disabled={recordSale.isPending}
            className="px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {recordSale.isPending ? 'Recording...' : 'Record Sale'}
          </button>
          <button
            type="button"
            onClick={() => navigate('/sales')}
            className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
        </div>
      </form>
    </div>
  );
}
