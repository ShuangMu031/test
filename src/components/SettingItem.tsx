// 设置项组件
import React from 'react';

interface SettingItemProps {
  label: string;
  type: 'toggle' | 'select' | 'input';
  value: boolean | string;
  onChange: (value: boolean | string) => void;
  options?: { label: string; value: string }[];
  placeholder?: string;
  description?: string;
  disabled?: boolean;
}

const SettingItem: React.FC<SettingItemProps> = ({ 
  label, 
  type, 
  value, 
  onChange, 
  options, 
  placeholder, 
  description, 
  disabled = false 
}) => {
  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-2">
        <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
          {label}
        </label>
        {type === 'toggle' && (
          <button
            onClick={() => !disabled && onChange(!(value as boolean))}
            className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${(value as boolean) ? 'bg-blue-500' : 'bg-gray-300'} ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            disabled={disabled}
          >
            <span
              className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${(value as boolean) ? 'translate-x-6' : 'translate-x-1'}`}
            />
          </button>
        )}
        {type === 'select' && (
          <select
            value={value as string}
            onChange={(e) => !disabled && onChange(e.target.value)}
            className={`px-3 py-1 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            disabled={disabled}
          >
            {options?.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        )}
        {type === 'input' && (
          <input
            type="text"
            value={value as string}
            onChange={(e) => !disabled && onChange(e.target.value)}
            placeholder={placeholder}
            className={`px-3 py-1 rounded-md border border-gray-300 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-900 dark:text-white text-sm ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
            disabled={disabled}
          />
        )}
      </div>
      {description && (
        <p className="text-xs text-gray-500 dark:text-gray-400 ml-0">
          {description}
        </p>
      )}
    </div>
  );
};

export default SettingItem;