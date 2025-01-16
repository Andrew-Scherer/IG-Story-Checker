import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import Button from '../../../src/components/common/Button';

describe('Button Component', () => {
  it('renders with default props', () => {
    const { getByRole } = render(<Button>Click Me</Button>);
    const button = getByRole('button');
    expect(button).toBeInTheDocument();
    expect(button).toHaveTextContent('Click Me');
    expect(button).not.toBeDisabled();
    expect(button).toHaveClass('button');
  });

  it('handles click events', () => {
    const handleClick = jest.fn();
    const { getByRole } = render(
      <Button onClick={handleClick}>Click Me</Button>
    );
    
    fireEvent.click(getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('supports disabled state', () => {
    const handleClick = jest.fn();
    const { getByRole } = render(
      <Button disabled onClick={handleClick}>
        Click Me
      </Button>
    );
    
    const button = getByRole('button');
    expect(button).toBeDisabled();
    
    fireEvent.click(button);
    expect(handleClick).not.toHaveBeenCalled();
  });

  it('applies variant classes', () => {
    const { getByRole } = render(
      <Button variant="primary">Primary Button</Button>
    );
    
    const button = getByRole('button');
    expect(button).toHaveClass('button', 'button--primary');
  });

  it('applies size classes', () => {
    const { getByRole } = render(
      <Button size="large">Large Button</Button>
    );
    
    const button = getByRole('button');
    expect(button).toHaveClass('button', 'button--large');
  });

  it('merges custom className with default classes', () => {
    const { getByRole } = render(
      <Button className="custom-class">Custom Button</Button>
    );
    
    const button = getByRole('button');
    expect(button).toHaveClass('button', 'custom-class');
  });

  it('forwards additional props to button element', () => {
    const { getByRole } = render(
      <Button type="submit" data-testid="test-button">
        Submit Button
      </Button>
    );
    
    const button = getByRole('button');
    expect(button).toHaveAttribute('type', 'submit');
    expect(button).toHaveAttribute('data-testid', 'test-button');
  });

  it('renders with loading state', () => {
    const { getByRole, getByTestId } = render(
      <Button loading>Loading Button</Button>
    );
    
    const button = getByRole('button');
    expect(button).toBeDisabled();
    expect(getByTestId('loading-spinner')).toBeInTheDocument();
  });

  it('handles keyboard navigation', () => {
    const handleClick = jest.fn();
    const { getByRole } = render(
      <Button onClick={handleClick}>Keyboard Button</Button>
    );
    
    const button = getByRole('button');
    button.focus();
    expect(button).toHaveFocus();
    
    fireEvent.keyDown(button, { key: 'Enter' });
    expect(handleClick).toHaveBeenCalledTimes(1);
    
    fireEvent.keyDown(button, { key: ' ' });
    expect(handleClick).toHaveBeenCalledTimes(2);
  });
});
