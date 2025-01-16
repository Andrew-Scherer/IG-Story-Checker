import React, { useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';
import classNames from 'classnames';
import './Modal.scss';

const Modal = ({
  children,
  className,
  closeButtonText = 'Close',
  footer,
  isOpen,
  onClose,
  size = 'medium',
  title
}) => {
  const handleEscape = useCallback((event) => {
    if (event.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = 'hidden';
      document.addEventListener('keydown', handleEscape);
    }

    return () => {
      document.body.style.overflow = '';
      document.removeEventListener('keydown', handleEscape);
    };
  }, [isOpen, handleEscape]);

  if (!isOpen) return null;

  const handleBackdropClick = (event) => {
    if (event.target === event.currentTarget) {
      onClose();
    }
  };

  return (
    <div
      className="modal-backdrop"
      onClick={handleBackdropClick}
      data-testid="modal-backdrop"
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
        className={classNames(
          'modal',
          `modal--${size}`,
          className
        )}
      >
        <div className="modal__header">
          <h2 id="modal-title" className="modal__title">
            {title}
          </h2>
          <button
            type="button"
            className="modal__close"
            onClick={onClose}
            aria-label={closeButtonText}
          >
            {closeButtonText}
          </button>
        </div>

        <div className="modal__content">
          {children}
        </div>

        {footer && (
          <div className="modal__footer">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

Modal.propTypes = {
  /** Modal content */
  children: PropTypes.node.isRequired,
  /** Additional class names */
  className: PropTypes.string,
  /** Close button text */
  closeButtonText: PropTypes.string,
  /** Footer content */
  footer: PropTypes.node,
  /** Controls modal visibility */
  isOpen: PropTypes.bool.isRequired,
  /** Close handler */
  onClose: PropTypes.func.isRequired,
  /** Modal size variant */
  size: PropTypes.oneOf(['small', 'medium', 'large']),
  /** Modal title */
  title: PropTypes.string.isRequired
};

export default Modal;
