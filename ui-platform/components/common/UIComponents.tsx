/**
 * Reusable UI Components
 * Common components for the platform
 */

import React from "react";

// Card Component
export interface CardProps {
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
  style?: React.CSSProperties;
  headerAction?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  title,
  description,
  children,
  className = "",
  style,
  headerAction,
}) => (
  <div className={`bg-gray-800 rounded-lg border border-gray-700 p-6 ${className}`} style={style}>
    {(title || headerAction) && (
      <div className="flex items-start justify-between mb-4">
        <div>
          {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
          {description && <p className="text-sm text-gray-400 mt-1">{description}</p>}
        </div>
        {headerAction && <div>{headerAction}</div>}
      </div>
    )}
    {children}
  </div>
);

// Stat Component
export interface StatProps {
  label: string;
  value: string | number;
  unit?: string;
  trend?: "up" | "down" | "stable";
  trendValue?: string;
  icon?: React.ReactNode;
  className?: string;
}

export const Stat: React.FC<StatProps> = ({
  label,
  value,
  unit,
  trend,
  trendValue,
  icon,
  className = "",
}) => (
  <div className={`bg-gray-800 rounded-lg border border-gray-700 p-4 ${className}`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-sm text-gray-400">{label}</p>
        <p className="text-2xl font-bold text-white mt-2">{value}</p>
        {unit && <p className="text-xs text-gray-500">{unit}</p>}
      </div>
      {icon && <div className="text-2xl">{icon}</div>}
    </div>
    {trend && trendValue && (
      <p
        className={`text-xs mt-3 ${
          trend === "up"
            ? "text-green-400"
            : trend === "down"
            ? "text-red-400"
            : "text-gray-400"
        }`}
      >
        {trend === "up" ? "📈" : trend === "down" ? "📉" : "➡️"} {trendValue}
      </p>
    )}
  </div>
);

// Button Component
export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  children,
  className = "",
  ...props
}) => {
  const baseClasses =
    "font-medium rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed";

  const variantClasses = {
    primary: "bg-blue-600 hover:bg-blue-700 text-white",
    secondary: "bg-gray-700 hover:bg-gray-600 text-white",
    danger: "bg-red-600 hover:bg-red-700 text-white",
  };

  const sizeClasses = {
    sm: "px-3 py-1 text-sm",
    md: "px-4 py-2 text-base",
    lg: "px-6 py-3 text-lg",
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? "⏳" : children}
    </button>
  );
};

// Loading Spinner
export interface LoadingProps {
  size?: "sm" | "md" | "lg";
  text?: string;
}

export const Loading: React.FC<LoadingProps> = ({ size = "md", text }) => {
  const sizeClass = {
    sm: "w-4 h-4",
    md: "w-8 h-8",
    lg: "w-12 h-12",
  };

  return (
    <div className="flex flex-col items-center justify-center py-8">
      <div
        className={`${sizeClass[size]} border-4 border-gray-700 border-t-blue-500 rounded-full animate-spin`}
      />
      {text && <p className="text-sm text-gray-400 mt-3">{text}</p>}
    </div>
  );
};

// Error Alert
export interface ErrorAlertProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
}

export const ErrorAlert: React.FC<ErrorAlertProps> = ({
  title,
  message,
  onDismiss,
}) => (
  <div className="bg-red-900 border border-red-700 rounded-lg p-4 mb-4">
    <div className="flex items-start justify-between">
      <div>
        {title && <h3 className="font-semibold text-red-200">{title}</h3>}
        <p className="text-sm text-red-100">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-200 hover:text-red-100 ml-2"
        >
          ✕
        </button>
      )}
    </div>
  </div>
);

// Success Alert
export interface SuccessAlertProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
}

export const SuccessAlert: React.FC<SuccessAlertProps> = ({
  title,
  message,
  onDismiss,
}) => (
  <div className="bg-green-900 border border-green-700 rounded-lg p-4 mb-4">
    <div className="flex items-start justify-between">
      <div>
        {title && <h3 className="font-semibold text-green-200">{title}</h3>}
        <p className="text-sm text-green-100">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-green-200 hover:text-green-100 ml-2"
        >
          ✕
        </button>
      )}
    </div>
  </div>
);

// Warning Alert
export interface WarningAlertProps {
  title?: string;
  message: string;
  onDismiss?: () => void;
}

export const WarningAlert: React.FC<WarningAlertProps> = ({
  title,
  message,
  onDismiss,
}) => (
  <div className="bg-yellow-900 border border-yellow-700 rounded-lg p-4 mb-4">
    <div className="flex items-start justify-between">
      <div>
        {title && <h3 className="font-semibold text-yellow-200">{title}</h3>}
        <p className="text-sm text-yellow-100">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-yellow-200 hover:text-yellow-100 ml-2"
        >
          ✕
        </button>
      )}
    </div>
  </div>
);

// Modal Component
export interface ModalProps {
  isOpen: boolean;
  title: string;
  onClose: () => void;
  children: React.ReactNode;
  footer?: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  title,
  onClose,
  children,
  footer,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-800 rounded-lg border border-gray-700 max-w-md w-full">
        <div className="flex items-center justify-between p-6 border-b border-gray-700">
          <h2 className="text-xl font-bold">{title}</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            ✕
          </button>
        </div>
        <div className="p-6">{children}</div>
        {footer && (
          <div className="p-6 border-t border-gray-700 flex gap-2 justify-end">
            {footer}
          </div>
        )}
      </div>
    </div>
  );
};

// Empty State Component
export interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon = "📭",
  title,
  description,
  action,
}) => (
  <div className="flex flex-col items-center justify-center py-12">
    <div className="text-4xl mb-3">{icon}</div>
    <h3 className="text-lg font-semibold text-white mb-1">{title}</h3>
    {description && <p className="text-sm text-gray-400 mb-4">{description}</p>}
    {action && <div>{action}</div>}
  </div>
);

// Progress Bar Component
export interface ProgressBarProps {
  value: number;
  max?: number;
  label?: string;
  showPercentage?: boolean;
  color?: "blue" | "green" | "yellow" | "red";
  size?: "sm" | "md" | "lg";
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  max = 100,
  label,
  showPercentage = true,
  color = "blue",
  size = "md",
}) => {
  const percentage = (value / max) * 100;

  const colorClasses = {
    blue: "bg-blue-600",
    green: "bg-green-600",
    yellow: "bg-yellow-600",
    red: "bg-red-600",
  };

  const sizeClasses = {
    sm: "h-1",
    md: "h-2",
    lg: "h-3",
  };

  return (
    <div>
      {(label || showPercentage) && (
        <div className="flex items-center justify-between mb-2">
          {label && <p className="text-sm text-gray-300">{label}</p>}
          {showPercentage && (
            <p className="text-sm text-gray-400">{percentage.toFixed(1)}%</p>
          )}
        </div>
      )}
      <div className={`w-full bg-gray-700 rounded-full overflow-hidden ${sizeClasses[size]}`}>
        <div
          className={`${colorClasses[color]} h-full transition-all duration-300`}
          style={{ width: `${Math.min(percentage, 100)}%` }}
        />
      </div>
    </div>
  );
};

// Table Component
export interface TableColumn {
  key: string;
  label: string;
  sortable?: boolean;
  align?: "left" | "center" | "right";
  render?: (value: unknown, row: unknown) => React.ReactNode;
}

export interface TableProps {
  columns: TableColumn[];
  data: Array<Record<string, unknown>>;
  loading?: boolean;
  error?: string;
  emptyMessage?: string;
}

export const Table: React.FC<TableProps> = ({
  columns,
  data,
  loading = false,
  error,
  emptyMessage = "No data available",
}) => {
  if (loading) return <Loading text="Loading data..." />;
  if (error) return <ErrorAlert message={error} />;
  if (data.length === 0) return <EmptyState title={emptyMessage} />;

  return (
    <div className="overflow-x-auto">
      <table className="w-full">
        <thead className="bg-gray-800 border-b border-gray-700">
          <tr>
            {columns.map((col) => (
              <th
                key={col.key}
                className={`px-4 py-3 text-left text-sm font-semibold text-gray-300 ${
                  col.align === "center"
                    ? "text-center"
                    : col.align === "right"
                    ? "text-right"
                    : ""
                }`}
              >
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.map((row, rowIndex) => (
            <tr
              key={rowIndex}
              className="border-b border-gray-700 hover:bg-gray-800 transition-colors"
            >
              {columns.map((col) => (
                <td
                  key={`${rowIndex}-${col.key}`}
                  className={`px-4 py-3 text-sm text-gray-100 ${
                    col.align === "center"
                      ? "text-center"
                      : col.align === "right"
                      ? "text-right"
                      : ""
                  }`}
                >
                  {col.render
                    ? col.render(row[col.key], row)
                    : String(row[col.key] || "-")}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
