import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Upload } from 'lucide-react';
import { productService } from '../services/product.service';
import type { ImportResult } from '../types/product.types';

export function ProductImportPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] ?? null;
    setSelectedFile(file);
    setResult(null);
    setImportError(null);
  };

  const handleImport = async () => {
    if (!selectedFile) return;
    setIsLoading(true);
    setImportError(null);
    setResult(null);
    try {
      const importResult = await productService.import(selectedFile);
      setResult(importResult);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Import failed');
    } finally {
      setIsLoading(false);
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

      <h1 className="text-2xl font-bold text-gray-900 mb-6">Import Products</h1>

      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-5 mb-6 max-w-2xl">
        <h2 className="text-sm font-semibold text-blue-900 mb-2">CSV Format</h2>
        <p className="text-sm text-blue-800 mb-2">
          Upload a CSV file with the following columns:
        </p>
        <div className="space-y-1 text-sm text-blue-800">
          <div>
            <span className="font-medium">Required:</span>{' '}
            <code className="bg-blue-100 px-1 rounded">name</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">sku</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">unit_price</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">cost_price</code>
          </div>
          <div>
            <span className="font-medium">Optional:</span>{' '}
            <code className="bg-blue-100 px-1 rounded">barcode</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">description</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">min_stock_level</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">unit_of_measure</code>,{' '}
            <code className="bg-blue-100 px-1 rounded">tax_rate</code>
          </div>
          <p className="mt-2 text-xs text-blue-700">
            Prices should be in paisa (integer). Existing SKUs will be skipped.
          </p>
        </div>
      </div>

      {/* File input */}
      <div className="max-w-2xl space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Select CSV File</label>
          <input
            ref={fileInputRef}
            type="file"
            accept=".csv"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-600 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
          />
          {selectedFile && (
            <p className="mt-1 text-xs text-gray-500">{selectedFile.name}</p>
          )}
        </div>

        <button
          onClick={handleImport}
          disabled={!selectedFile || isLoading}
          className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white text-sm font-medium rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Upload size={15} />
          {isLoading ? 'Importing...' : 'Import'}
        </button>

        {/* Error */}
        {importError && (
          <div className="rounded-md bg-red-50 border border-red-200 p-3">
            <p className="text-sm text-red-700">{importError}</p>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="rounded-lg border border-gray-200 bg-white p-5 space-y-3">
            <h2 className="text-sm font-semibold text-gray-900">Import Complete</h2>
            <div className="flex gap-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{result.created}</p>
                <p className="text-xs text-gray-500">Created</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-yellow-600">{result.skipped}</p>
                <p className="text-xs text-gray-500">Skipped</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-red-600">{result.errors.length}</p>
                <p className="text-xs text-gray-500">Errors</p>
              </div>
            </div>

            {result.errors.length > 0 && (
              <div>
                <h3 className="text-sm font-medium text-gray-700 mb-2">Errors</h3>
                <div className="overflow-auto max-h-64 border border-red-100 rounded-md">
                  <table className="w-full text-xs">
                    <thead className="bg-red-50">
                      <tr>
                        <th className="text-left px-3 py-2 text-red-700">Row</th>
                        <th className="text-left px-3 py-2 text-red-700">SKU</th>
                        <th className="text-left px-3 py-2 text-red-700">Reason</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-red-100">
                      {result.errors.map((e, i) => (
                        <tr key={i} className="bg-white">
                          <td className="px-3 py-2 text-gray-600">{e.row}</td>
                          <td className="px-3 py-2 font-mono text-gray-600">{e.sku}</td>
                          <td className="px-3 py-2 text-gray-600">{e.reason}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
