import React from 'react';
import './Spinner.scss';

function Spinner({ size = 'medium', inline = false, light = false }) {
  const sizeClass = {
    small: 'spinner--small',
    medium: 'spinner--medium',
    large: 'spinner--large'
  }[size];

  return (
    <div 
      className={`
        spinner 
        ${sizeClass} 
        ${inline ? 'spinner--inline' : ''} 
        ${light ? 'spinner--light' : ''}
      `}
    >
      <div className="spinner__circle" />
    </div>
  );
}

export default Spinner;
