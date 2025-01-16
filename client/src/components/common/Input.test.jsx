import React, { useState } from 'react';
import { render, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import Input from './Input';

describe('Input Component', () => {
  it('renders correctly', () => {
    const { container } = render(<Input />);
    expect(container.querySelector('input')).toBeInTheDocument();
  });

  it('handles value changes', () => {
    // Create a wrapper component to properly test controlled input behavior
    const TestComponent = () => {
      const [value, setValue] = useState('');
      return (
        <Input
          value={value}
          onChange={(e) => setValue(e.target.value)}
        />
      );
    };

    const { container } = render(<TestComponent />);
    const input = container.querySelector('input');
    
    fireEvent.change(input, { target: { value: 'new value' } });
    expect(input.value).toBe('new value');
  });

  it('calls onChange handler', () => {
    const handleChange = jest.fn();
    const { container } = render(
      <Input value="" onChange={handleChange} />
    );
    
    const input = container.querySelector('input');
    fireEvent.change(input, { target: { value: 'test' } });
    
    expect(handleChange).toHaveBeenCalledTimes(1);
    expect(handleChange.mock.calls[0][0].target.value).toBe('test');
  });

  it('displays error state', () => {
    const { container, getByText } = render(
      <Input error="Invalid input" />
    );
    
    const input = container.querySelector('input');
    expect(input).toHaveClass('input--error');
    expect(getByText('Invalid input')).toBeInTheDocument();
  });

  it('supports disabled state', () => {
    const { container } = render(
      <Input disabled />
    );
    
    const input = container.querySelector('input');
    expect(input).toBeDisabled();
  });

  it('applies size classes', () => {
    const { container } = render(
      <Input size="large" />
    );
    
    const input = container.querySelector('input');
    expect(input).toHaveClass('input--large');
  });

  it('supports different types', () => {
    const { container } = render(
      <Input type="password" />
    );
    
    const input = container.querySelector('input');
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
    const { getByText } = render(
      <Input
        prefix={<span>$</span>}
        suffix={<span>.00</span>}
      />
    );
    
    expect(getByText('$')).toBeInTheDocument();
    expect(getByText('.00')).toBeInTheDocument();
  });

  it('handles focus and blur events', () => {
    const handleFocus = jest.fn();
    const handleBlur = jest.fn();
    const { container } = render(
      <Input onFocus={handleFocus} onBlur={handleBlur} />
    );
    
    const input = container.querySelector('input');
    fireEvent.focus(input);
    expect(handleFocus).toHaveBeenCalledTimes(1);
    
    fireEvent.blur(input);
    expect(handleBlur).toHaveBeenCalledTimes(1);
  });

  it('forwards ref to input element', () => {
    const ref = React.createRef();
    const { container } = render(<Input ref={ref} />);
    
    expect(ref.current).toBe(container.querySelector('input'));
  });
});
