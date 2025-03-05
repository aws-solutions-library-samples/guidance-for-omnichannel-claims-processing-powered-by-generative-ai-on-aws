// components/ValueWithLabel.tsx
import React from 'react';
import { Box, SpaceBetween } from '@cloudscape-design/components';

interface ValueWithLabelProps {
  label: string;
  children: React.ReactNode;
  labelFontSize?: 'body-s' | 'body-m' | 'heading-xs' | 'heading-s';
  valueFontSize?: 'body-s' | 'body-m' | 'heading-xs' | 'heading-s';
  color?: string;
  labelColor?: string;
}

const ValueWithLabel: React.FC<ValueWithLabelProps> = ({
  label,
  children,
  labelFontSize = 'body-s',
  valueFontSize = 'body-m',
  color,
  labelColor = 'text-label'
}) => {
  return (
    <SpaceBetween size="xs">
      <Box color={labelColor} fontSize={labelFontSize}>
        {label}
      </Box>
      <Box fontSize={valueFontSize} color={color}>
        {children}
      </Box>
    </SpaceBetween>
  );
};

export default ValueWithLabel;
