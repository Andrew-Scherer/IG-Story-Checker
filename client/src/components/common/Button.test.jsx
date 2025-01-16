import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Button from './Button';

describe('Button Component', () => {
  it('renders children correctly', () => {
    const { getByRole } = render(<Button>Click me</Button>);
    expect(getByRole('button')).toHaveTextContent('Click me');
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    const { getByRole } = render(
      <Button onClick={handleClick}>Click me</Button>
    );
    
    fireEvent.click(getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('supports disabled state', () => {
    const handleClick = jest.fn();
    const { getByRole } = render(
      <Button disabled onClick={handleClick}>
        Click me
      </Button>
    );
    
    const button = getByRole('button');
    expect(button).toBeDisabled();
    
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('shows loading state', () => {
    const { getByRole, getByTestId } = render(
      <Button loading>Click me</Button>
    );
    
    expect(getByTestId('loading-spinner')).toBeInTheDocument();
    expect(getByRole('button')).toHaveTextContent('Click me');
    expect(getByRole('button')).toBeDisabled();
  });

  it('applies variant classes', () => {
    const { getByRole } = render(
      <Button variant="primary">Primary Button</Button>
    );
    
    expect(getByRole('button')).toHaveClass('button--primary');
  });

  it('applies size classes', () => {
    const { getByRole } = render(
      <Button size="large">Large Button</Button>
    );
    
    expect(getByRole('button')).toHaveClass('button--large');
  });
});
