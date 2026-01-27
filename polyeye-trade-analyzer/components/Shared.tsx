import React from 'react';

export const Card: React.FC<{ children: React.ReactNode; className?: string; title?: string }> = ({ children, className = "", title }) => (
  <div className={`bg-white rounded-[32px] p-8 border border-black ${className}`}>
    {title && (
      <h3 className="text-sm font-light tracking-widest uppercase text-gray-500 mb-6">{title}</h3>
    )}
    {children}
  </div>
);

export const Button: React.FC<React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'outline' }> = ({ 
  children, 
  variant = 'primary', 
  className = "", 
  ...props 
}) => {
  const baseStyles = "px-8 py-4 rounded-full font-light uppercase tracking-wider transition-all duration-300 flex items-center justify-center gap-2";
  
  const variants = {
    primary: "bg-black text-white border border-black hover:bg-white hover:text-black",
    secondary: "bg-white text-black border border-black hover:bg-gray-100",
    outline: "border border-black text-black hover:bg-black hover:text-white"
  };

  return (
    <button className={`${baseStyles} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
};

export const Input: React.FC<React.InputHTMLAttributes<HTMLInputElement> & { label?: string }> = ({ label, className = "", ...props }) => (
  <div className="w-full">
    {label && <label className="block text-xs font-light uppercase tracking-widest text-gray-500 mb-2 ml-4">{label}</label>}
    <input 
      className={`w-full bg-transparent border border-black rounded-full px-6 py-4 text-black font-light placeholder-gray-400 focus:outline-none focus:bg-white transition-all ${className}`}
      {...props}
    />
  </div>
);

export const SectionHeader: React.FC<{ title: string; subtitle?: string }> = ({ title, subtitle }) => (
  <div className="mb-10">
    <h2 className="text-4xl md:text-6xl font-thin uppercase tracking-tighter leading-[0.9] text-black">
      {title}
    </h2>
    {subtitle && (
      <p className="mt-4 text-lg text-gray-500 font-light max-w-md">
        {subtitle}
      </p>
    )}
  </div>
);