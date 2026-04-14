import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useForm, useFieldArray, useWatch, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2, ArrowLeft, Tag, X } from 'lucide-react';
import type { AxiosError } from 'axios';
import { useRecordSale } from '../hooks/useSales';
import { ProductSearchSelect } from '../components/ui/ProductSearchSelect';
import { promotionService } from '../services/promotion.service';
import type { SalePayload } from '../types/sale.types';
import type { EligiblePromotion } from '../types/promotion.types';

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

function displayPromotionValue(promo: EligiblePromotion): string {
  if (promo.type === 'percentage') return `${promo.value}%`;
  if (promo.type === 'fixed') return `৳${(promo.value / 100).toFixed(2)} off`;
  return 'BOGO';
}

export function RecordSalePage() {
  const navigate = useNavigate();
  const recordSale = useRecordSale();

  // Promotion picker state
  const [selectedPromotion, setSelectedPromotion] = useState<EligiblePromotion | null>(null);
  const [eligiblePromotions, setEligiblePromotions] = useState<EligiblePromotion[]>([]);
  const [promoPickerOpen, setPromoPickerOpen] = useState(false);
  const [promoLoading, setPromoLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Track which row indexes have an auto-populated (catalogue) price
  const [autoPricedRows, setAutoPricedRows] = useState<Set<number>>(new Set());

  const {
    register,
    control,
    handleSubmit,
    setValue,
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

  // Subtotal in ৳ (form stores ৳, not paisa)
  const subtotalTaka = (watchedItems ?? []).reduce((sum, item) => {
    const price = typeof item.unit_price === 'number' && !isNaN(item.unit_price) ? item.unit_price : 0;
    const qty = typeof item.quantity === 'number' && !isNaN(item.quantity) ? item.quantity : 0;
    return sum + price * qty;
  }, 0);

  const subtotalPaisa = Math.round(subtotalTaka * 100);

  // Whenever items change, clear the selected promotion and re-fetch eligible ones
  useEffect(() => {
    setSelectedPromotion(null);
    setEligiblePromotions([]);

    const validItems = (watchedItems ?? []).filter(
      (i) => i.product_id && typeof i.quantity === 'number' && i.quantity > 0 &&
             typeof i.unit_price === 'number' && i.unit_price > 0,
    );
    if (validItems.length === 0 || subtotalPaisa === 0 || isNaN(subtotalPaisa)) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setPromoLoading(true);
      try {
        const apiItems = validItems.map((i) => ({
          product_id: i.product_id,
          quantity: i.quantity as number,
          unit_price: Math.round((i.unit_price as number) * 100),
        }));
        const result = await promotionService.getEligible(subtotalPaisa, apiItems);
        setEligiblePromotions(result);
      } catch {
        setEligiblePromotions([]);
      } finally {
        setPromoLoading(false);
      }
    }, 500);

    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [JSON.stringify(watchedItems)]);

  const discountTaka = selectedPromotion
    ? selectedPromotion.discount_amount / 100
    : 0;
  const totalTaka = subtotalTaka - discountTaka;

  const fmt = (n: number) => (isNaN(n) ? '0.00' : n.toFixed(2));

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
      promotion_id: selectedPromotion?.id ?? undefined,
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
            <span className="col-span-5">Product</span>
            <span className="col-span-2">Qty</span>
            <span className="col-span-3">Unit Price ৳</span>
            <span className="col-span-1">Total</span>
            <span className="col-span-1"></span>
          </div>

          <div className="space-y-2">
            {fields.map((field, index) => {
              const item = watchedItems?.[index];
              const qty = typeof item?.quantity === 'number' && !isNaN(item.quantity) ? item.quantity : 0;
              const unitPrice = typeof item?.unit_price === 'number' && !isNaN(item.unit_price) ? item.unit_price : 0;
              const rowTotal = unitPrice * qty;

              return (
                <div key={field.id} className="grid grid-cols-12 gap-2 items-start">
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
                          onProductSelect={(product) => {
                            // Auto-populate unit price from catalogue (paisa → taka)
                            setValue(
                              `items.${index}.unit_price`,
                              product.unit_price / 100,
                              { shouldValidate: true, shouldDirty: true },
                            );
                            setAutoPricedRows((prev) => new Set(prev).add(index));
                          }}
                        />
                      )}
                    />
                    {errors.items?.[index]?.product_id && (
                      <p className="mt-0.5 text-xs text-red-600">
                        {errors.items[index]?.product_id?.message}
                      </p>
                    )}
                  </div>

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

                  <div className="col-span-3">
                    <div className="relative">
                      <input
                        type="number"
                        min={0}
                        step="0.01"
                        {...register(`items.${index}.unit_price`, {
                          valueAsNumber: true,
                          onChange: () => {
                            // User manually edited the price — clear the auto-price indicator
                            if (autoPricedRows.has(index)) {
                              setAutoPricedRows((prev) => {
                                const next = new Set(prev);
                                next.delete(index);
                                return next;
                              });
                            }
                          },
                        })}
                        className="w-full px-2 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                      />
                      {autoPricedRows.has(index) && (
                        <span
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-blue-500"
                          title="Auto-populated from product catalogue"
                        >
                          auto
                        </span>
                      )}
                    </div>
                    {errors.items?.[index]?.unit_price && (
                      <p className="mt-0.5 text-xs text-red-600">
                        {errors.items[index]?.unit_price?.message}
                      </p>
                    )}
                  </div>

                  <div className="col-span-1 py-2 font-mono text-sm text-gray-700">
                    ৳{fmt(rowTotal)}
                  </div>

                  <div className="col-span-1 flex justify-center">
                    <button
                      type="button"
                      onClick={() => {
                        remove(index);
                        setAutoPricedRows((prev) => {
                          const next = new Set<number>();
                          prev.forEach((i) => { if (i !== index) next.add(i > index ? i - 1 : i); });
                          return next;
                        });
                      }}
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

          {/* Totals summary */}
          <div className="mt-4 pt-4 border-t border-gray-100 space-y-1">
            <div className="flex justify-end text-sm text-gray-600">
              <span className="w-32 text-right">Subtotal</span>
              <span className="w-28 text-right font-mono">৳{fmt(subtotalTaka)}</span>
            </div>
            {selectedPromotion && (
              <div className="flex justify-end text-sm text-green-700">
                <span className="w-32 text-right">Discount</span>
                <span className="w-28 text-right font-mono">−৳{fmt(discountTaka)}</span>
              </div>
            )}
            <div className="flex justify-end text-sm font-semibold text-gray-900">
              <span className="w-32 text-right">Total</span>
              <span className="w-28 text-right font-mono">৳{fmt(totalTaka)}</span>
            </div>
          </div>
        </div>

        {/* Promotion Picker */}
        {subtotalPaisa > 0 && (
          <div className="rounded-md border border-gray-200 bg-gray-50 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <Tag size={15} className="text-gray-500" />
                <span className="text-sm font-medium text-gray-700">Promotion</span>
                {promoLoading && (
                  <span className="text-xs text-gray-400">Checking eligibility…</span>
                )}
              </div>
              {selectedPromotion ? (
                <button
                  type="button"
                  onClick={() => setSelectedPromotion(null)}
                  className="flex items-center gap-1 text-xs text-red-600 hover:text-red-800"
                >
                  <X size={12} /> Remove
                </button>
              ) : (
                eligiblePromotions.length > 0 && (
                  <button
                    type="button"
                    onClick={() => setPromoPickerOpen((v) => !v)}
                    className="text-xs text-blue-600 hover:text-blue-800 font-medium"
                  >
                    {promoPickerOpen ? 'Hide' : `View ${eligiblePromotions.length} eligible`}
                  </button>
                )
              )}
            </div>

            {/* Applied promotion badge */}
            {selectedPromotion ? (
              <div className="flex items-center gap-3 rounded-md bg-green-50 border border-green-200 px-3 py-2">
                <span className="text-sm font-medium text-green-800">{selectedPromotion.name}</span>
                <span className="text-xs text-green-600 font-mono">
                  {displayPromotionValue(selectedPromotion)}
                </span>
                <span className="ml-auto text-sm font-semibold text-green-700 font-mono">
                  −৳{(selectedPromotion.discount_amount / 100).toFixed(2)}
                </span>
              </div>
            ) : !promoLoading && eligiblePromotions.length === 0 ? (
              <p className="text-xs text-gray-400">No eligible promotions for this sale.</p>
            ) : null}

            {/* Eligible promotions list */}
            {promoPickerOpen && !selectedPromotion && eligiblePromotions.length > 0 && (
              <ul className="mt-2 space-y-1.5">
                {eligiblePromotions.map((promo) => (
                  <li key={promo.id}>
                    <button
                      type="button"
                      onClick={() => {
                        setSelectedPromotion(promo);
                        setPromoPickerOpen(false);
                      }}
                      className="w-full flex items-center justify-between rounded-md border border-gray-200 bg-white px-3 py-2 text-sm hover:border-blue-400 hover:bg-blue-50 transition-colors"
                    >
                      <div className="flex items-center gap-2 min-w-0">
                        <span className="font-medium text-gray-900 truncate">{promo.name}</span>
                        <span className="text-xs text-gray-500 shrink-0">
                          {displayPromotionValue(promo)}
                        </span>
                        {promo.auto_apply && (
                          <span className="text-xs px-1.5 py-0.5 rounded bg-amber-100 text-amber-700 shrink-0">
                            Auto
                          </span>
                        )}
                      </div>
                      <span className="font-semibold text-green-700 font-mono shrink-0 ml-3">
                        −৳{(promo.discount_amount / 100).toFixed(2)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

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
