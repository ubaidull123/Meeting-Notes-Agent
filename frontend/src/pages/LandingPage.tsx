import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { LoadingSpinner } from '../components/ui/LoadingState';
import { LandingNavbar } from '../components/landing/LandingNavbar';
import { HeroSection } from '../components/landing/HeroSection';
import { ProductPreview } from '../components/landing/ProductPreview';
import { HowItWorks } from '../components/landing/HowItWorks';
import { FeaturesSection } from '../components/landing/FeaturesSection';
import { TechStackSection } from '../components/landing/TechStackSection';
import { FinalCTA } from '../components/landing/FinalCTA';
import { LandingFooter } from '../components/landing/LandingFooter';

export const LandingPage: React.FC = () => {
  const { isAuthenticated, isLoading, isAdmin } = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <LoadingSpinner size="lg" label="Loading..." />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to={isAdmin ? '/admin' : '/dashboard'} replace />;
  }

  return (
    <div className="min-h-screen flex flex-col bg-background text-foreground selection:bg-teal-500 selection:text-white">
      <LandingNavbar />
      <main className="flex-1">
        <HeroSection />
        <ProductPreview />
        <HowItWorks />
        <FeaturesSection />
        <TechStackSection />
        <FinalCTA />
      </main>
      <LandingFooter />
    </div>
  );
};
