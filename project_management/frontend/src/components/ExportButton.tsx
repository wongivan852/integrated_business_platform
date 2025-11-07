import React from 'react';
import { Download } from 'lucide-react';

interface ExportButtonProps {
  onClick: () => void;
  label?: string;
  variant?: 'primary' | 'secondary' | 'success';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
}

const ExportButton: React.FC<ExportButtonProps> = ({
  onClick,
  label = 'Export CSV',
  variant = 'primary',
  size = 'md',
  disabled = false
}) => {
  const variantClasses = {
    primary: 'bg-blue-600 hover:bg-blue-700 text-white',
    secondary: 'bg-gray-600 hover:bg-gray-700 text-white',
    success: 'bg-green-600 hover:bg-green-700 text-white'
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        flex items-center gap-2 rounded-lg font-medium
        transition-all duration-200 shadow-sm hover:shadow-md
        ${variantClasses[variant]}
        ${sizeClasses[size]}
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'cursor-pointer'}
      `}
    >
      <Download size={size === 'sm' ? 16 : size === 'lg' ? 24 : 20} />
      <span>{label}</span>
    </button>
  );
};

export default ExportButton;
