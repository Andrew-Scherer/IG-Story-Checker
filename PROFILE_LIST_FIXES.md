# Required Fixes

## Current Issues
1. Niche list missing from left side
2. Pagination missing
3. Profile list missing

## Architectural Changes Needed

1. ProfileList.jsx should be simplified to:
   - Remove duplicate action buttons (these already exist in NicheFeed)
   - Keep only the table and pagination components
   - Ensure pagination appears when profiles are loaded

2. NicheFeed.jsx is correctly structured but needs to ensure:
   - Sidebar with niche list remains visible
   - Action buttons stay in the header
   - ProfileList component renders in the main content area

These changes will restore the proper layout while maintaining the existing functionality.