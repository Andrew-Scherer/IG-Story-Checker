import React from 'react';
import classNames from 'classnames';
import PropTypes from 'prop-types';
import './Button.scss';

const Button = React.forwardRef(({
  children,
  className,
  disabled = false,
  loading = false,
  onClick,
  size = 'medium',
  variant = 'default',
  type = 'button',
  ...props
}, ref) => {
  const handleClick = (event) => {
    if (!disabled && !loading && onClick) {
      onClick(event);
    }
  };

  const handleKeyDown = (event) => {
    if (!disabled && !loading && onClick && (event.key === 'Enter' || event.key === ' ')) {
      event.preventDefault();
      onClick(event);
    }
  };

  const buttonClasses = classNames(
    'button',
    `button--${variant}`,
    `button--${size}`,
    {
      'button--loading': loading,
      'button--disabled': disabled || loading
    },
    className
  );

  return (
    <button
      ref={ref}
      className={buttonClasses}
      disabled={disabled || loading}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      type={type}
      {...props}
    >
      {loading && (
        <span 
          className="button__spinner"
          data-testid="loading-spinner"
          aria-hidden="true"
        />
      )}
      <span className={loading ? 'button__text button__text--loading' : 'button__text'}>
        {children}
      </span>
    </button>
  );
});

Button.displayName = 'Button';

Button.propTypes = {
  /** Button content */
  children: PropTypes.node.isRequired,
  /** Additional class names */
  className: PropTypes.string,
  /** Disabled state */
  disabled: PropTypes.bool,
  /** Loading state */
  loading: PropTypes.bool,
  /** Click handler */
  onClick: PropTypes.func,
  /** Button size */
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  /** Button variant */
  variant: PropTypes.oneOf(['default', 'primary', 'secondary', 'danger']),
  /** Button type */
  type: PropTypes.oneOf(['button', 'submit', 'reset'])
};

export default Button;
