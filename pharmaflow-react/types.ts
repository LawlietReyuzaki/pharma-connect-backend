
export type Page = 'landing' | 'register' | 'admin-login' | 'admin-dashboard';

export interface NavItem {
  label: string;
  href: string;
}

export interface PharmacyProfile {
  id: number;
  name: string;
  address: string;
  owner: string;
  traffic: string;
  revenue: string;
  apiCost: string;
  hostingCost: string;
  phone: string;
  email: string;
  regNumber: string;
  lat: number;
  lng: number;
  doctors: number;
}

export interface Metric {
  title: string;
  value: string;
  trend: string;
  isPositive: boolean;
}

export interface Feature {
  id: number;
  title: string;
  description: string;
  iconName: string;
}

export interface Step {
  id: number;
  title: string;
  description: string;
}

export interface Doctor {
  id: number;
  name: string;
  specialty: string;
  available: boolean;
}

export interface PharmacyGCost {
  id: number;
  name: string;
  domain: string;
  webAppUrl: string;
  databaseInfo: string;
  mau: string; // Monthly Active Users
  dailyApiCalls: number;
  totalApiCalls: number;
  tokenUsage: string;
  hostingCost: number;
  servingCost: number;
  storageCost: number;
  totalCost: number;
  status: 'High Usage' | 'Normal' | 'Low Usage';
}