import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import Table from '../../../src/components/common/Table';

describe('Table Component', () => {
  const mockData = [
    { id: 1, name: 'John', age: 25 },
    { id: 2, name: 'Jane', age: 30 },
    { id: 3, name: 'Bob', age: 35 }
  ];

  const mockColumns = [
    { key: 'name', title: 'Name' },
    { key: 'age', title: 'Age' }
  ];

  it('renders with basic data and columns', () => {
    const { getByText } = render(
      <Table data={mockData} columns={mockColumns} />
    );
    
    // Check headers
    expect(getByText('Name')).toBeInTheDocument();
    expect(getByText('Age')).toBeInTheDocument();
    
    // Check data
    expect(getByText('John')).toBeInTheDocument();
    expect(getByText('25')).toBeInTheDocument();
  });

  it('handles sorting when clicking headers', () => {
    const onSort = jest.fn();
    const { getByText } = render(
      <Table
        data={mockData}
        columns={mockColumns}
        onSort={onSort}
        sortable
      />
    );
    
    fireEvent.click(getByText('Name'));
    expect(onSort).toHaveBeenCalledWith('name', 'asc');
    
    fireEvent.click(getByText('Name'));
    expect(onSort).toHaveBeenCalledWith('name', 'desc');
  });

  it('handles row selection', () => {
    const onSelect = jest.fn();
    const { getByRole } = render(
      <Table
        data={mockData}
        columns={mockColumns}
        selectable
        onSelect={onSelect}
      />
    );
    
    const checkbox = getByRole('checkbox');
    fireEvent.click(checkbox);
    expect(onSelect).toHaveBeenCalledWith([mockData[0]]);
  });

  it('handles pagination', () => {
    const onPageChange = jest.fn();
    const { getByText } = render(
      <Table
        data={mockData}
        columns={mockColumns}
        pagination
        pageSize={2}
        onPageChange={onPageChange}
      />
    );
    
    const nextButton = getByText('Next');
    fireEvent.click(nextButton);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });

  it('displays empty state message', () => {
    const { getByText } = render(
      <Table
        data={[]}
        columns={mockColumns}
        emptyMessage="No data available"
      />
    );
    
    expect(getByText('No data available')).toBeInTheDocument();
  });

  it('applies custom row classes', () => {
    const rowClassName = (row) => row.age > 30 ? 'highlight' : '';
    const { getByText } = render(
      <Table
        data={mockData}
        columns={mockColumns}
        rowClassName={rowClassName}
      />
    );
    
    const bobRow = getByText('Bob').closest('tr');
    expect(bobRow).toHaveClass('highlight');
  });

  it('renders custom cell renderers', () => {
    const columns = [
      ...mockColumns,
      {
        key: 'actions',
        title: 'Actions',
        render: (row) => (
          <button data-testid={`action-${row.id}`}>
            Edit
          </button>
        )
      }
    ];
    
    const { getByTestId } = render(
      <Table data={mockData} columns={columns} />
    );
    
    expect(getByTestId('action-1')).toBeInTheDocument();
  });

  it('handles row click events', () => {
    const onRowClick = jest.fn();
    const { getByText } = render(
      <Table
        data={mockData}
        columns={mockColumns}
        onRowClick={onRowClick}
      />
    );
    
    fireEvent.click(getByText('John'));
    expect(onRowClick).toHaveBeenCalledWith(mockData[0]);
  });
});
