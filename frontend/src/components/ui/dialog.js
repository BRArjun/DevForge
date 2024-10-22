// import React from 'react';
// import * as DialogPrimitive from '@radix-ui/react-dialog';

// export const Dialog = DialogPrimitive.Root;
// export const DialogTrigger = DialogPrimitive.Trigger;
// export const DialogContent = React.forwardRef((props, forwardedRef) => (
//   <DialogPrimitive.Portal>
//     <DialogPrimitive.Overlay className="fixed inset-0 bg-black bg-opacity-50" />
//     <DialogPrimitive.Content ref={forwardedRef} className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-auto" {...props} />
//   </DialogPrimitive.Portal>
// ));
// export const DialogHeader = (props) => <div className="mb-4" {...props} />;
// export const DialogTitle = (props) => <h2 className="text-xl font-bold" {...props} />;



import React from 'react';
import * as DialogPrimitive from '@radix-ui/react-dialog';
import { VisuallyHidden } from '@radix-ui/react-visually-hidden';

export const Dialog = DialogPrimitive.Root;
export const DialogTrigger = DialogPrimitive.Trigger;

export const DialogContent = React.forwardRef(({ title, description, children, ...props }, forwardedRef) => (
  <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 bg-black bg-opacity-50" />
    <DialogPrimitive.Content 
      ref={forwardedRef} 
      className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white rounded-lg p-6 w-full max-w-md max-h-screen overflow-auto" 
      {...props}
    >
      <VisuallyHidden asChild>
        <DialogPrimitive.Title>{title}</DialogPrimitive.Title>
      </VisuallyHidden>
      {description && (
        <DialogPrimitive.Description>{description}</DialogPrimitive.Description>
      )}
      {children}
    </DialogPrimitive.Content>
  </DialogPrimitive.Portal>
));

export const DialogHeader = (props) => <div className="mb-4" {...props} />;
export const DialogTitle = DialogPrimitive.Title;