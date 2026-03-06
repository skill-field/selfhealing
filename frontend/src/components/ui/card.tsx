import type { ReactNode } from 'react';
import { clsx } from 'clsx';

interface CardProps {
  title?: string;
  description?: string;
  children?: ReactNode;
  className?: string;
}

export function Card({ title, description, children, className }: CardProps) {
  return (
    <div
      className={clsx(
        'rounded-xl border border-gray-800 bg-gray-900 p-5',
        className,
      )}
    >
      {title && (
        <h3 className="text-sm font-semibold text-gray-100">{title}</h3>
      )}
      {description && (
        <p className="mt-1 text-xs text-gray-400">{description}</p>
      )}
      {(title || description) && children && <div className="mt-4">{children}</div>}
      {!title && !description && children}
    </div>
  );
}
