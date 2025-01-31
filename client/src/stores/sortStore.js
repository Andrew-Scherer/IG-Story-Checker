import { create } from 'zustand';

// Map frontend column names to backend column names
const COLUMN_MAPPING = {
  'stats': 'detection_rate',
  'niche': 'niche__name',
  'detection_rate': 'detection_rate',
  // Other columns map 1:1
  'username': 'username',
  'status': 'status',
  'last_checked': 'last_checked',
  'last_detected': 'last_detected',
  'total_detections': 'total_detections',
  'total_checks': 'total_checks'
};

export const useSortStore = create((set, get) => ({
  // State
  sortColumn: null,
  sortDirection: 'asc',
  sortableColumns: [
    'username',
    'niche',
    'status',
    'last_checked',
    'last_detected',
    'detection_rate'  // Changed from 'stats' to 'detection_rate'
  ],

  // Actions
  setSort: (column, direction = 'asc') => {
    if (!COLUMN_MAPPING[column]) {
      console.warn(`Unknown sort column: ${column}`);
      return;
    }
    set({
      sortColumn: column,
      sortDirection: direction
    });
  },

  toggleDirection: () => {
    const { sortDirection } = get();
    set({
      sortDirection: sortDirection === 'asc' ? 'desc' : 'asc'
    });
  },

  reset: () => {
    set({
      sortColumn: null,
      sortDirection: 'asc'
    });
  },

  // Get params for API requests
  getQueryParams: () => {
    const { sortColumn, sortDirection } = get();
    const params = {};

    if (sortColumn) {
      // Map frontend column to backend column
      const apiSortColumn = COLUMN_MAPPING[sortColumn];
      if (apiSortColumn) {
        params.sort_by = apiSortColumn;
        params.sort_direction = sortDirection;
      }
    }

    return params;
  }
}));