import React from 'react';

export const Button = ({ children, ...props }) => (
  <button className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600" {...props}>
    {children}
  </button>
);

export const DeleteButton = ({ children, ...props }) => (
  <button className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600" {...props}>
    {children}
  </button>
);

export const RenameButton = ({ children, ...props }) => (
  <button className="px-4 py-2 bg-yellow-500 text-white rounded hover:bg-yellow-600" {...props}>
    {children}
  </button>
);
