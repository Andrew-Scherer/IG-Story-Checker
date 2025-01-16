import React from 'react';
import { render, fireEvent } from '@testing-library/react';
import Input from '../../../src/components/common/Input';

describe('Input Component', () => {
  it('renders with default props', () => {
    const { getByRole } = render(<Input />);
    const input = getByRole('textbox');
    expect(input).toBeInTheDocument();
    expect(input).toHaveClass('input');
    expect(input).not.toBeDisabled();
  });

  it('handles value changes', () => {
    const handleChange = jest.fn();
    const { getByRole } = render(
      <Input value="test" onChange={handleChange} />
    );
    
    const input = getByRole('textbox');
    fireEvent.change(input, { target: { value: 'new value' } });
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange.mock.calls[0][0].target.value).toBe('new value');
  });

  it('displays error state', () => {
    const { getByRole, getByText } = render(
      <Input error="Invalid input" />
    );
    
    const input = getByRole('textbox');
    expect(input).toHaveClass('input', 'input--error');
    expect(getByText('Invalid input')).toBeInTheDocument();
  });

  it('supports disabled state', () => {
    const handleChange = jest.fn();
    const { getByRole } = render(
      <Input disabled onChange={handleChange} />
    );
    
    const input = getByRole('textbox');
    expect(input).toBeDisabled();
    
    fireEvent.change(input, { target: { value: 'test' } });
    expect(handleChange).not.toHaveBeenCalled();
  });

  it('applies size classes', () => {
    const { getByRole } = render(
      <Input size="large" />
    );
    
    const input = getByRole('textbox');
    expect(input).toHaveClass('input', 'input--large');
  });

  it('supports different types', () => {
    const { getByRole } = render(
      <Input type="password" />
    );
    
    const input = getByRole('textbox');
    expect(input).toHaveAttribute('type', 'password');
  });

  it('displays placeholder text', () => {
    const placeholder = 'Enter text here';
    const { getByPlaceholderText } = render(
      <Input placeholder={placeholder} />
    );
    
    expect(getByPlaceholderText(placeholder)).toBeInTheDocument();
  });

  it('supports prefix and suffix elements', () => {
    const { getByTestId, getByText } = render(
      <Input
        prefix={<span data-testid="prefix">$</span>}
        suffix={<span data-testid="suffix">.00</span>}
      />
    );
    
    expect(getByTestId('prefix')).toBeInTheDocument();
    expect(getByTestId('suffix')).toBeInTheDocument();
    expect(getByText('$')).toBeInTheDocument();
    expect(getByText('.00')).toBeInTheDocument();
  });

  it('handles focus and blur events', () => {
    const handleFocus = jest.fn();
    const handleBlur = jest.fn();
    const { getByRole } = render(
      <Input onFocus={handleFocus} onBlur={handleBlur} />
    );
    
    const input = getByRole('textbox');
    fireEvent.focus(input);
    expect(handleFocus).toHaveBeenCalledTimes(1);
    
    fireEvent.blur(input);
    expect(handleBlur).toHaveBeenCalledTimes(1);
  });

  it('merges custom className with default classes', () => {
    const { getByRole } = render(
      <Input className="custom-class" />
    );
    
    const input = getByRole('textbox');
    expect(input).toHaveClass('input', 'custom-class');
  });
});
