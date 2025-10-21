'use client';

import React, { createContext, useContext, ReactNode } from 'react';
import { Environment } from '../types/environment';

interface EnvironmentContextType {
  environment: Environment;
}

const EnvironmentContext = createContext<EnvironmentContextType | undefined>(undefined);

interface EnvironmentProviderProps {
  children: ReactNode;
  environment: Environment;
}

export const EnvironmentProvider: React.FC<EnvironmentProviderProps> = ({
  children,
  environment,
}) => {
  return (
    <EnvironmentContext.Provider value={{ environment }}>{children}</EnvironmentContext.Provider>
  );
};

export const useEnvironment = (): Environment => {
  const context = useContext(EnvironmentContext);
  if (!context) {
    throw new Error('useEnvironment must be used within EnvironmentProvider');
  }
  return context.environment;
};
