import type { InputHTMLAttributes } from 'react'

interface FormInputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
  helper?: string
}

export default function FormInput({ label, error, helper, id, ...inputProps }: FormInputProps) {
  const inputId = id ?? label.toLowerCase().replace(/\s+/g, '-')

  return (
    <div>
      <label htmlFor={inputId} className="mb-1 block text-xs font-semibold">
        {label}
      </label>
      <input
        id={inputId}
        {...inputProps}
        className={`w-full rounded-lg border bg-surface px-3 py-2 outline-none focus:border-primary ${
          error ? 'border-danger' : 'border-line'
        }`}
      />
      {error ? (
        <p className="mt-1 text-xs text-danger">{error}</p>
      ) : helper ? (
        <p className="mt-1 text-xs text-secondary">{helper}</p>
      ) : null}
    </div>
  )
}
