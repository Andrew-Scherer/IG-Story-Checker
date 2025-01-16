import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';
import Input from '../common/Input';
import Button from '../common/Button';
import './StoryTargets.scss';

const StoryTargets = ({ targets, onUpdate }) => {
  const [values, setValues] = useState(targets);
  const [errors, setErrors] = useState({});
  const [message, setMessage] = useState({ text: '', type: '' });

  useEffect(() => {
    setValues(targets);
  }, [targets]);

  const validateField = (name, value, newValues = values) => {
    const newErrors = {};

    switch (name) {
      case 'minStories':
      case 'maxStories':
        if (value < 0) {
          newErrors[name] = 'Must be a positive number';
        } else if (name === 'maxStories' && value < newValues.minStories) {
          newErrors[name] = 'Maximum must be greater than minimum';
        } else if (name === 'minStories' && newValues.maxStories < value) {
          newErrors.maxStories = 'Maximum must be greater than minimum';
        }
        break;

      case 'minFollowers':
      case 'maxFollowers':
        if (value < 1000) {
          newErrors[name] = 'Must be at least 1000';
        } else if (name === 'maxFollowers' && value < newValues.minFollowers) {
          newErrors[name] = 'Maximum must be greater than minimum';
        } else if (name === 'minFollowers' && newValues.maxFollowers < value) {
          newErrors.maxFollowers = 'Maximum must be greater than minimum';
        }
        break;

      case 'minEngagement':
      case 'maxEngagement':
        if (value < 0) {
          newErrors[name] = 'Must be a positive number';
        } else if (name === 'maxEngagement' && value < newValues.minEngagement) {
          newErrors[name] = 'Maximum must be greater than minimum';
        } else if (name === 'minEngagement' && newValues.maxEngagement < value) {
          newErrors.maxEngagement = 'Maximum must be greater than minimum';
        }
        break;

      default:
        break;
    }

    return { isValid: Object.keys(newErrors).length === 0, errors: newErrors };
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    const numValue = value === '' ? '' : parseFloat(value);
    const newValues = { ...values, [name]: numValue };
    const { isValid, errors: newErrors } = validateField(name, numValue, newValues);
    
    // Clear any previous errors for this field and its related field
    const relatedField = name.startsWith('min') ? name.replace('min', 'max') : name.replace('max', 'min');
    setErrors(prevErrors => {
      const { [name]: _, [relatedField]: __, ...rest } = prevErrors;
      return { ...rest, ...newErrors };
    });

    setValues(newValues);

    if (isValid) {
      onUpdate(newValues);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage({ text: '', type: '' });

    // Validate all fields
    const newErrors = {};
    let isValid = true;

    Object.entries(values).forEach(([name, value]) => {
      const { isValid: fieldValid, errors } = validateField(name, value, values);
      if (!fieldValid) {
        isValid = false;
        Object.assign(newErrors, errors);
      }
    });

    setErrors(newErrors);

    if (isValid) {
      try {
        await onUpdate(values);
        setMessage({ text: 'Settings saved successfully', type: 'success' });
      } catch (error) {
        setMessage({ text: 'Failed to save settings', type: 'error' });
      }
    }
  };

  return (
    <form className="story-targets" onSubmit={handleSubmit}>
      <div className="story-targets__section">
        <h3>Story Count</h3>
        <div className="story-targets__field-group">
          <Input
            type="number"
            name="minStories"
            id="minStories"
            label="Minimum Stories"
            value={values.minStories}
            onChange={handleChange}
            error={errors.minStories}
          />
          <Input
            type="number"
            name="maxStories"
            id="maxStories"
            label="Maximum Stories"
            value={values.maxStories}
            onChange={handleChange}
            error={errors.maxStories}
          />
        </div>
      </div>

      <div className="story-targets__section">
        <h3>Follower Count</h3>
        <div className="story-targets__field-group">
          <Input
            type="number"
            name="minFollowers"
            id="minFollowers"
            label="Minimum Followers"
            value={values.minFollowers}
            onChange={handleChange}
            error={errors.minFollowers}
          />
          <Input
            type="number"
            name="maxFollowers"
            id="maxFollowers"
            label="Maximum Followers"
            value={values.maxFollowers}
            onChange={handleChange}
            error={errors.maxFollowers}
          />
        </div>
      </div>

      <div className="story-targets__section">
        <h3>Engagement Rate</h3>
        <div className="story-targets__field-group">
          <Input
            type="number"
            name="minEngagement"
            id="minEngagement"
            label="Minimum Engagement"
            value={values.minEngagement}
            onChange={handleChange}
            error={errors.minEngagement}
            step="0.1"
          />
          <Input
            type="number"
            name="maxEngagement"
            id="maxEngagement"
            label="Maximum Engagement"
            value={values.maxEngagement}
            onChange={handleChange}
            error={errors.maxEngagement}
            step="0.1"
          />
        </div>
      </div>

      {message.text && (
        <div className={`story-targets__message story-targets__message--${message.type}`}>
          {message.text}
        </div>
      )}

      <div className="story-targets__actions">
        <Button type="submit">Save</Button>
      </div>
    </form>
  );
};

StoryTargets.propTypes = {
  targets: PropTypes.shape({
    minStories: PropTypes.number.isRequired,
    maxStories: PropTypes.number.isRequired,
    minFollowers: PropTypes.number.isRequired,
    maxFollowers: PropTypes.number.isRequired,
    minEngagement: PropTypes.number.isRequired,
    maxEngagement: PropTypes.number.isRequired
  }).isRequired,
  onUpdate: PropTypes.func.isRequired
};

export default StoryTargets;
