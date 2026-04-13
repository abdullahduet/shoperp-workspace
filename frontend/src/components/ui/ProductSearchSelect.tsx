import { useState, useEffect, useRef, useCallback } from 'react';
import { productService } from '../../services/product.service';
import type { Product } from '../../types/product.types';

const PAGE_SIZE = 5;

// ─── Shared fetch hook ───────────────────────────────────────────────────────

interface DropdownState {
  options: Product[];
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
}

interface UseProductDropdownReturn extends DropdownState {
  query: string;
  setQuery: (q: string) => void;
  loadInitial: () => void;
  loadMore: () => void;
  reset: () => void;
}

/**
 * Manages server-side search + infinite scroll for product dropdowns.
 * - On loadInitial(): fetches page 1 with no search term (first 5 products).
 * - On setQuery(q): debounces 300ms, resets to page 1, fetches with search term.
 * - On loadMore(): fetches next page and appends to existing options.
 * Cancels in-flight requests on new query to prevent race conditions.
 */
function useProductDropdown(excludeIds: string[] = []): UseProductDropdownReturn {
  const [options, setOptions] = useState<Product[]>([]);
  const [query, setQueryState] = useState('');
  const [hasMore, setHasMore] = useState(false);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);

  const abortRef = useRef<AbortController | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Track the query that was actually fetched so loadMore uses the right term
  const fetchedQueryRef = useRef('');
  const fetchedPageRef = useRef(1);

  const fetchPage = useCallback(
    async (q: string, pg: number, append: boolean) => {
      // Cancel any previous in-flight request
      abortRef.current?.abort();
      const controller = new AbortController();
      abortRef.current = controller;

      if (append) {
        setLoadingMore(true);
      } else {
        setLoading(true);
      }

      try {
        const res = await productService.list({
          search: q || undefined,
          is_active: true,
          limit: PAGE_SIZE,
          page: pg,
        });

        if (controller.signal.aborted) return;

        const filtered = res.data.filter((p) => !excludeIds.includes(p.id));
        setOptions((prev) => (append ? [...prev, ...filtered] : filtered));
        setHasMore(pg < res.pagination.total_pages);
        fetchedQueryRef.current = q;
        fetchedPageRef.current = pg;
      } catch {
        if (!controller.signal.aborted) {
          if (!append) setOptions([]);
          setHasMore(false);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
          setLoadingMore(false);
        }
      }
    },
    // excludeIds identity changes on every render if caller passes inline array,
    // so we intentionally omit it — callers that need exclusion pass a stable ref.
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const setQuery = useCallback(
    (q: string) => {
      setQueryState(q);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        fetchPage(q, 1, false);
      }, 300);
    },
    [fetchPage],
  );

  const loadInitial = useCallback(() => {
    // Only fetch if we haven't loaded anything yet for this session
    if (options.length === 0 && !loading) {
      fetchPage('', 1, false);
    }
  }, [options.length, loading, fetchPage]);

  const loadMore = useCallback(() => {
    if (loadingMore || !hasMore) return;
    const nextPage = fetchedPageRef.current + 1;
    fetchPage(fetchedQueryRef.current, nextPage, true);
  }, [loadingMore, hasMore, fetchPage]);

  const reset = useCallback(() => {
    abortRef.current?.abort();
    if (debounceRef.current) clearTimeout(debounceRef.current);
    setOptions([]);
    setQueryState('');
    setHasMore(false);
    setLoading(false);
    setLoadingMore(false);
    fetchedQueryRef.current = '';
    fetchedPageRef.current = 1;
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return { options, query, setQuery, loading, loadingMore, hasMore, loadInitial, loadMore, reset };
}

// ─── Shared dropdown list ────────────────────────────────────────────────────

interface DropdownListProps {
  options: Product[];
  loading: boolean;
  loadingMore: boolean;
  hasMore: boolean;
  query: string;
  onSelect: (product: Product) => void;
  onLoadMore: () => void;
}

function DropdownList({
  options,
  loading,
  loadingMore,
  hasMore,
  query,
  onSelect,
  onLoadMore,
}: DropdownListProps) {
  const sentinelRef = useRef<HTMLLIElement>(null);

  // IntersectionObserver watches the sentinel element at the bottom of the list
  useEffect(() => {
    const sentinel = sentinelRef.current;
    if (!sentinel) return;

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasMore && !loadingMore) {
          onLoadMore();
        }
      },
      { threshold: 0.1 },
    );

    observer.observe(sentinel);
    return () => observer.disconnect();
  }, [hasMore, loadingMore, onLoadMore]);

  return (
    <ul className="absolute z-50 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-52 overflow-y-auto text-sm">
      {loading && <li className="px-3 py-2 text-gray-400">Loading…</li>}
      {!loading && options.length === 0 && (
        <li className="px-3 py-2 text-gray-400">
          {query ? 'No products found' : 'No products available'}
        </li>
      )}
      {options.map((p) => (
        <li
          key={p.id}
          onMouseDown={() => onSelect(p)}
          className="px-3 py-2 cursor-pointer hover:bg-blue-50 flex items-center justify-between gap-2"
        >
          <span className="font-medium text-gray-900 truncate">{p.name}</span>
          <span className="text-xs text-gray-400 font-mono shrink-0">{p.sku}</span>
        </li>
      ))}
      {/* Infinite scroll sentinel */}
      <li ref={sentinelRef} className="px-3 py-1 text-center text-xs text-gray-400">
        {loadingMore ? 'Loading more…' : hasMore ? '' : options.length > 0 ? 'End of results' : ''}
      </li>
    </ul>
  );
}

// ─── Single-select ───────────────────────────────────────────────────────────

interface ProductSearchSelectProps {
  value: string;
  onChange: (productId: string) => void;
  onBlur?: () => void;
  onProductSelect?: (product: Product) => void;
  placeholder?: string;
  hasError?: boolean;
  disabled?: boolean;
}

/**
 * Searchable autocomplete for a single product_id.
 * - Loads first 5 products on focus.
 * - Fetches from backend on every keystroke (debounced 300ms).
 * - Infinite scroll loads more in batches of 5.
 * - Submits the product UUID; displays "Name  SKU" when selected.
 */
export function ProductSearchSelect({
  value,
  onChange,
  onBlur,
  onProductSelect,
  placeholder = 'Search product…',
  hasError = false,
  disabled = false,
}: ProductSearchSelectProps) {
  const [open, setOpen] = useState(false);
  const [selectedLabel, setSelectedLabel] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);

  const { options, query, setQuery, loading, loadingMore, hasMore, loadInitial, loadMore, reset } =
    useProductDropdown();

  // Clear label when value is reset externally (e.g. form reset)
  useEffect(() => {
    if (!value) {
      setSelectedLabel('');
    }
  }, [value]);

  function handleFocus() {
    if (selectedLabel) return; // already has a selection — don't reopen
    setOpen(true);
    loadInitial();
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    const q = e.target.value;
    if (!q) {
      onChange('');
      setSelectedLabel('');
    }
    setOpen(true);
    setQuery(q);
  }

  function handleSelect(product: Product) {
    onChange(product.id);
    onProductSelect?.(product);
    setSelectedLabel(`${product.name}  ${product.sku}`);
    setOpen(false);
    reset();
  }

  function handleBlur() {
    setTimeout(() => {
      setOpen(false);
      onBlur?.();
    }, 150);
  }

  // Clear selection when user starts editing the display value
  function handleSelectedLabelChange(e: React.ChangeEvent<HTMLInputElement>) {
    setSelectedLabel('');
    onChange('');
    const q = e.target.value;
    setOpen(true);
    setQuery(q);
  }

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  const borderClass = hasError ? 'border-red-500' : 'border-gray-300';

  return (
    <div ref={containerRef} className="relative">
      {selectedLabel ? (
        // Show the selected label; typing clears it and re-enters search mode
        <input
          type="text"
          value={selectedLabel}
          onChange={handleSelectedLabelChange}
          onBlur={handleBlur}
          disabled={disabled}
          className={`w-full px-2 py-2 border ${borderClass} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400`}
          autoComplete="off"
        />
      ) : (
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          disabled={disabled}
          className={`w-full px-2 py-2 border ${borderClass} rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-50 disabled:text-gray-400`}
          autoComplete="off"
        />
      )}
      {open && !selectedLabel && (
        <DropdownList
          options={options}
          loading={loading}
          loadingMore={loadingMore}
          hasMore={hasMore}
          query={query}
          onSelect={handleSelect}
          onLoadMore={loadMore}
        />
      )}
    </div>
  );
}

// ─── Multi-select ────────────────────────────────────────────────────────────

interface ProductMultiSelectProps {
  value: string[];
  onChange: (ids: string[]) => void;
  placeholder?: string;
}

/**
 * Multi-select variant: shows selected products as removable tags.
 * Same server-side search + infinite scroll behaviour as ProductSearchSelect.
 * Used in PromotionsPage for applies_to='specific'.
 */
export function ProductMultiSelect({
  value,
  onChange,
  placeholder = 'Search and add products…',
}: ProductMultiSelectProps) {
  const [open, setOpen] = useState(false);
  const [selectedProducts, setSelectedProducts] = useState<Product[]>([]);
  const [resolving, setResolving] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);
  const resolvedRef = useRef<Set<string>>(new Set());

  // excludeIds must be stable — we pass the ref value directly inside fetchPage
  // by using a ref so the hook's memoised fetchPage doesn't need to re-create.
  const excludeIdsRef = useRef<string[]>(value);
  excludeIdsRef.current = value;

  const { options, query, setQuery, loading, loadingMore, hasMore, loadInitial, loadMore, reset } =
    useProductDropdown(excludeIdsRef.current);

  // Resolve product names for IDs that aren't already in selectedProducts.
  // Runs when value changes (e.g. edit modal opens with pre-existing product_ids).
  useEffect(() => {
    const unresolved = value.filter((id) => !resolvedRef.current.has(id));
    if (unresolved.length === 0) return;

    setResolving(true);
    Promise.all(unresolved.map((id) => productService.getById(id).catch(() => null)))
      .then((results) => {
        const fetched = results.filter((p): p is Product => p !== null);
        fetched.forEach((p) => resolvedRef.current.add(p.id));
        setSelectedProducts((prev) => {
          const map = new Map(prev.map((p) => [p.id, p]));
          fetched.forEach((p) => map.set(p.id, p));
          // Preserve order from value array
          return value
            .map((id) => map.get(id) ?? ({ id, name: id, sku: '' } as Product))
            .filter((p) => value.includes(p.id));
        });
      })
      .finally(() => setResolving(false));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value.join(',')]);

  function handleFocus() {
    setOpen(true);
    loadInitial();
  }

  function handleInputChange(e: React.ChangeEvent<HTMLInputElement>) {
    setOpen(true);
    setQuery(e.target.value);
  }

  function handleSelect(product: Product) {
    onChange([...value, product.id]);
    resolvedRef.current.add(product.id);
    setSelectedProducts((prev) => [...prev, product]);
    setOpen(false);
    reset();
  }

  function handleRemove(id: string) {
    onChange(value.filter((v) => v !== id));
    setSelectedProducts((prev) => prev.filter((p) => p.id !== id));
  }

  function handleBlur() {
    setTimeout(() => setOpen(false), 150);
  }

  useEffect(() => {
    function onClickOutside(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener('mousedown', onClickOutside);
    return () => document.removeEventListener('mousedown', onClickOutside);
  }, []);

  // Filter out already-selected from displayed options
  const visibleOptions = options.filter((p) => !value.includes(p.id));

  return (
    <div ref={containerRef} className="space-y-2">
      {resolving && (
        <p className="text-xs text-gray-400">Loading products…</p>
      )}
      {!resolving && selectedProducts.length > 0 && (
        <div className="flex flex-wrap gap-1.5">
          {selectedProducts.map((p) => (
            <span
              key={p.id}
              className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-100 text-blue-800 text-xs rounded-full"
            >
              <span className="font-medium">{p.name !== p.id ? p.name : p.id.slice(0, 8)}</span>
              {p.sku && <span className="font-mono text-blue-600">{p.sku}</span>}
              <button
                type="button"
                onClick={() => handleRemove(p.id)}
                className="ml-0.5 text-blue-500 hover:text-blue-800 font-bold leading-none"
              >
                ×
              </button>
            </span>
          ))}
        </div>
      )}

      <div className="relative">
        <input
          type="text"
          value={query}
          onChange={handleInputChange}
          onFocus={handleFocus}
          onBlur={handleBlur}
          placeholder={placeholder}
          className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          autoComplete="off"
        />
        {open && (
          <DropdownList
            options={visibleOptions}
            loading={loading}
            loadingMore={loadingMore}
            hasMore={hasMore}
            query={query}
            onSelect={handleSelect}
            onLoadMore={loadMore}
          />
        )}
      </div>
    </div>
  );
}
