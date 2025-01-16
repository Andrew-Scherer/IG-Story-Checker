import React from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import './Input.scss';

const Input = React.forwardRef(({
  className,
  disabled = false,
  error,
  label,
  id,
  name,
  onChange,
  onFocus,
  onBlur,
  placeholder,
  prefix,
  size = 'medium',
  suffix,
  type = 'text',
  value = '',
  ...props
}, ref) => {
  const handleChange = (event) => {
    if (!disabled && onChange) {
      // Ensure we're passing the event with the correct value
    const newEvent = {
      ...event,
      target: {
        ...event.target,
        name: event.target.name,
        value: event.target.value
      }
    };
      onChange(newEvent);
    }
  };

  const inputClasses = classNames(
    'input',
    `input--${size}`,
    {
      'input--error': error,
      'input--disabled': disabled,
      'input--with-prefix': prefix,
      'input--with-suffix': suffix
    },
    className
  );

  const inputId = id || name;

  return (
    <div className="input-wrapper">
      {label && (
        <label htmlFor={inputId} className="input__label">
          {label}
        </label>
      )}
      {prefix && (
        <div className="input__prefix">
          {prefix}
        </div>
      )}
      
      <input
        ref={ref}
        id={inputId}
        className={inputClasses}
        disabled={disabled}
        onChange={handleChange}
        onFocus={onFocus}
        onBlur={onBlur}
        placeholder={placeholder}
        type={type}
        value={value}
        name={name}
        {...props}
      />
      
      {suffix && (
        <div className="input__suffix">
          {suffix}
        </div>
      )}
      
      {error && (
        <div className="input__error-message">
          {error}
        </div>
      )}
    </div>
  );
});

Input.displayName = 'Input';

Input.propTypes = {
  /** Additional class names */
  className: PropTypes.string,
  /** Disabled state */
  disabled: PropTypes.bool,
  /** Error message */
  error: PropTypes.string,
  /** Input label */
  label: PropTypes.string,
  /** Input ID (required if label is provided) */
  id: PropTypes.string,
  /** Input name */
  name: PropTypes.string,
  /** Change handler */
  onChange: PropTypes.func,
  /** Focus handler */
  onFocus: PropTypes.func,
  /** Blur handler */
  onBlur: PropTypes.func,
  /** Placeholder text */
  placeholder: PropTypes.string,
  /** Prefix element */
  prefix: PropTypes.node,
  /** Input size */
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  /** Suffix element */
  suffix: PropTypes.node,
  /** Input type */
  type: PropTypes.string,
  /** Input value */
  value: PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.number
  ])
};

export default Input;
