import { useQuery } from '@tanstack/react-query';
import { reportService } from '../services/report.service';

export function useDashboardSummary(enabled: boolean) {
  return useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => reportService.getDashboardSummary(),
    enabled,
  });
}

export function useDashboardTrends(enabled: boolean) {
  return useQuery({
    queryKey: ['dashboard-trends'],
    queryFn: () => reportService.getDashboardTrends(),
    enabled,
  });
}
