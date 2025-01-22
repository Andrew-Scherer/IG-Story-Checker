import React from 'react';
import Spinner from './Spinner';
import './Button.scss';

function Button({
  children,
  variant = 'primary',
  size = 'medium',
  disabled = false,
  loading = false,
  onClick,
  type = 'button',
  className = '',
  ...props
}) {
  const variantClass = {
    primary: 'button--primary',
    secondary: 'button--secondary',
    danger: 'button--danger',
    text: 'button--text'
  }[variant];

  const sizeClass = {
    small: 'button--small',
    medium: 'button--medium',
    large: 'button--large'
  }[size];

  const isDisabled = disabled || loading;

  return (
    <button
      type={type}
      className={`
        button 
        ${variantClass} 
        ${sizeClass}
        ${loading ? 'button--loading' : ''}
        ${className}
      `}
      disabled={isDisabled}
      onClick={!isDisabled ? onClick : undefined}
      {...props}
    >
      {loading && (
        <Spinner 
          size="small" 
          inline 
          light={variant === 'primary'} 
        />
      )}
      <span className={loading ? 'button__text--loading' : ''}>
        {children}
      </span>
    </button>
  );
}

export default Button;
