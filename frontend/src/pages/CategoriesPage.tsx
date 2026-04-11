import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Pencil, Trash2, Plus } from 'lucide-react';
import {
  useCategories,
  useCreateCategory,
  useUpdateCategory,
  useDeleteCategory,
} from '../hooks/useCategories';
import { useAuthStore } from '../store/auth.store';
import { LoadingSkeleton } from '../components/ui/LoadingSkeleton';
import { ErrorDisplay } from '../components/ui/ErrorDisplay';
import type { Category, CategoryFormValues } from '../types/category.types';

const categorySchema = z.object({
  name: z.string().min(1, 'Name is required'),
  description: z.string().optional().default(''),
  parent_id: z.string().optional().default(''),
  sort_order: z.number().int().min(0).default(0),
});

type CategorySchemaValues = z.infer<typeof categorySchema>;

interface CategoryModalProps {
  editing: Category | null;
  categories: Category[];
  onClose: () => void;
}

function CategoryModal({ editing, categories, onClose }: CategoryModalProps) {
  const createCategory = useCreateCategory();
  const updateCategory = useUpdateCategory();

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CategorySchemaValues>({
    resolver: zodResolver(categorySchema),
    defaultValues: editing
      ? {
          name: editing.name,
          description: editing.description ?? '',
          parent_id: editing.parent_id ?? '',
          sort_order: editing.sort_order,
        }
      : { name: '', description: '', parent_id: '', sort_order: 0 },
  });

  const isPending = createCategory.isPending || updateCategory.isPending;
  const mutationError = createCategory.error || updateCategory.error;

  const onSubmit = (values: CategorySchemaValues) => {
    const payload: Partial<CategoryFormValues> = {
      name: values.name,
      description: values.description ?? '',
      parent_id: values.parent_id || undefined,
      sort_order: values.sort_order,
    };

    if (editing) {
      updateCategory.mutate(
        { id: editing.id, data: payload },
        { onSuccess: onClose },
      );
    } else {
      createCategory.mutate(payload, { onSuccess: onClose });
    }
  };

  // Exclude self from parent options when editing
  const parentOptions = categories.filter((c) => c.id !== editing?.id);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="bg-white rounded-lg shadow-xl w-full max-w-md mx-4 p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          {editing ? 'Edit Category' : 'New Category'}
        </h2>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
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

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              {...register('description')}
              rows={3}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          {/* Parent Category */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Parent Category
            </label>
            <select
              {...register('parent_id')}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="">None</option>
              {parentOptions.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </div>

          {/* Sort Order */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Sort Order
            </label>
            <input
              type="number"
              {...register('sort_order', { valueAsNumber: true })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {errors.sort_order && (
              <p className="mt-1 text-xs text-red-600">{errors.sort_order.message}</p>
            )}
          </div>

          {/* Server error */}
          {mutationError && (
            <div className="rounded-md bg-red-50 border border-red-200 p-3">
              <p className="text-sm text-red-700">{mutationError.message}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-gray-700 border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isPending}
              className="px-4 py-2 text-sm text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isPending ? 'Saving...' : editing ? 'Save Changes' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export function CategoriesPage() {
  const [isOpen, setIsOpen] = useState(false);
  const [editing, setEditing] = useState<Category | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: categories, isLoading, isError, error } = useCategories();
  const deleteCategory = useDeleteCategory();
  const user = useAuthStore((state) => state.user);

  const handleNew = () => {
    setEditing(null);
    setIsOpen(true);
  };

  const handleEdit = (category: Category) => {
    setEditing(category);
    setIsOpen(true);
  };

  const handleClose = () => {
    setIsOpen(false);
    setEditing(null);
  };

  const handleDelete = (id: string) => {
    if (!window.confirm('Delete this category?')) return;
    setDeleteError(null);
    deleteCategory.mutate(id, {
      onError: (err) => setDeleteError(err.message),
    });
  };

  if (isLoading) return <LoadingSkeleton />;
  if (isError) return <ErrorDisplay message={error?.message ?? 'Failed to load categories'} />;

  const categoryList = categories ?? [];

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Categories</h1>
        <button
          onClick={handleNew}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700"
        >
          <Plus size={16} />
          New Category
        </button>
      </div>

      {/* Delete error */}
      {deleteError && (
        <p className="mb-4 text-sm text-red-600 bg-red-50 border border-red-200 rounded-md px-4 py-2">
          {deleteError}
        </p>
      )}

      {/* Empty state */}
      {categoryList.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-lg border border-gray-200">
          <p className="text-gray-500 mb-4">No categories yet.</p>
          <button
            onClick={handleNew}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 mx-auto"
          >
            <Plus size={16} />
            New Category
          </button>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Name
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Parent
                </th>
                <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Sort Order
                </th>
                <th className="text-right px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {categoryList.map((category) => {
                const parentName = category.parent_id
                  ? (categoryList.find((c) => c.id === category.parent_id)?.name ?? '—')
                  : '—';
                return (
                  <tr key={category.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 font-medium text-gray-900">{category.name}</td>
                    <td className="px-4 py-3 text-gray-600">{parentName}</td>
                    <td className="px-4 py-3 text-gray-600">{category.sort_order}</td>
                    <td className="px-4 py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          onClick={() => handleEdit(category)}
                          className="p-1.5 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded"
                          title="Edit"
                        >
                          <Pencil size={15} />
                        </button>
                        {user?.role === 'admin' && (
                          <button
                            onClick={() => handleDelete(category.id)}
                            disabled={deleteCategory.isPending}
                            className="p-1.5 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded disabled:opacity-50"
                            title="Delete"
                          >
                            <Trash2 size={15} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {/* Modal */}
      {isOpen && (
        <CategoryModal
          editing={editing}
          categories={categoryList}
          onClose={handleClose}
        />
      )}
    </div>
  );
}
