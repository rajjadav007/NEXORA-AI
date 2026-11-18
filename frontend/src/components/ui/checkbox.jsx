import React from 'react';
import { Check } from 'lucide-react';
import { cn } from '../../utils/cn';

export const Checkbox = React.forwardRef(({
  className,
  id,
  checked,
  defaultChecked,
  onChange,
  disabled = false,
  error = false,
  ...props
}, ref) => {
  const [isChecked, setIsChecked] = React.useState(defaultChecked || false);
  const controlled = checked !== undefined;
  const currentChecked = controlled ? checked : isChecked;

  const handleChange = (e) => {
    if (!controlled) {
      setIsChecked(e.target.checked);
    }
    if (onChange) {
      onChange(e);
    }
  };

  return (
    <label
      htmlFor={id}
      className={cn(
        'inline-flex items-center gap-2 select-none cursor-pointer',
        disabled && 'cursor-not-allowed opacity-60'
      )}
    >
      <div className="relative inline-flex items-center justify-center">
        <input
          type="checkbox"
          id={id}
          ref={ref}
          checked={currentChecked}
          onChange={handleChange}
          disabled={disabled}
          aria-invalid={error ? 'true' : undefined}
          className="peer sr-only"
          {...props}
        />
        <div
          className={cn(
            'h-5 w-5 rounded border transition-colors flex items-center justify-center',
            'peer-focus-visible:ring-2 peer-focus-visible:ring-primary peer-focus-visible:ring-offset-2',
            currentChecked
              ? 'bg-primary border-primary text-white'
              : 'bg-white border-slate-300 hover:border-slate-400',
            error && 'border-red-500',
            className
          )}
          aria-hidden="true"
        >
          {currentChecked && <Check className="h-3.5 w-3.5 stroke-[3]" />}
        </div>
      </div>
    </label>
  );
});

Checkbox.displayName = 'Checkbox';
