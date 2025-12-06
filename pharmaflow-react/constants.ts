
import { NavItem, PharmacyProfile, Feature, Step, Doctor, PharmacyGCost } from './types';

export const NAV_ITEMS: NavItem[] = [
  { label: 'Home', href: '#hero' },
  { label: 'Services', href: '#features' },
  { label: 'Platform', href: '#custom-domain' },
  { label: 'Pricing', href: '#pricing' },
];

export const SAMPLE_PHARMACIES: PharmacyProfile[] = [
  {
    id: 1,
    name: "Red Dot Pharmacy",
    address: "124 Queen St, NY",
    owner: "Dr. A. Silva",
    traffic: "12.5k/mo",
    revenue: "$45,200",
    apiCost: "$120",
    hostingCost: "$49",
    phone: "+1 (555) 123-4567",
    email: "contact@reddot.com",
    regNumber: "RX-99281-NY",
    lat: 40.7128,
    lng: -74.0060,
    doctors: 4
  },
  {
    id: 2,
    name: "Al Shifa Pharmacy",
    address: "89 Valley Rd, CA",
    owner: "James O'Connor",
    traffic: "8.2k/mo",
    revenue: "$32,100",
    apiCost: "$85",
    hostingCost: "$49",
    phone: "+1 (555) 987-6543",
    email: "info@alshifa-rx.com",
    regNumber: "RX-11234-CA",
    lat: 34.0522,
    lng: -118.2437,
    doctors: 2
  },
  {
    id: 3,
    name: "Prime Pharmacy",
    address: "44 Main Blvd, TX",
    owner: "Elena Ross",
    traffic: "22k/mo",
    revenue: "$88,400",
    apiCost: "$340",
    hostingCost: "$99",
    phone: "+1 (555) 444-2222",
    email: "support@primepharma.com",
    regNumber: "RX-55112-TX",
    lat: 29.7604,
    lng: -95.3698,
    doctors: 6
  }
];

export const FEATURES: Feature[] = [
  {
    id: 1,
    title: "AI Chatbot",
    description: "Every pharmacy gets its own custom chatbot + domain + API access. Automate patient queries instantly.",
    iconName: "Bot"
  },
  {
    id: 2,
    title: "Inventory Management",
    description: "Manage medicines, stock, expiry & reports. Keep track of every pill with real-time updates.",
    iconName: "Package"
  },
  {
    id: 3,
    title: "Doctor Appointment System",
    description: "Manage doctors, schedules & patients. Integrated directly with your pharmacy workflow.",
    iconName: "CalendarCheck"
  }
];

export const STEPS: Step[] = [
  {
    id: 1,
    title: "Register Pharmacy",
    description: "Sign up and create your digital pharmacy profile in minutes."
  },
  {
    id: 2,
    title: "Import Inventory",
    description: "Upload your product list or sync with your existing POS system."
  },
  {
    id: 3,
    title: "Configure AI",
    description: "Customize the chatbot to answer common patient questions."
  },
  {
    id: 4,
    title: "Go Live",
    description: "Start accepting orders and appointments online immediately."
  }
];

export const DOCTORS: Doctor[] = [
  {
    id: 1,
    name: "Dr. Sarah Chen",
    specialty: "Cardiologist",
    available: true
  },
  {
    id: 2,
    name: "Dr. Michael Ross",
    specialty: "Dermatologist",
    available: false
  },
  {
    id: 3,
    name: "Dr. Emily White",
    specialty: "Pediatrician",
    available: true
  },
  {
    id: 4,
    name: "Dr. James Wilson",
    specialty: "General Practitioner",
    available: true
  }
];

export const PHARMACY_G_COSTS: PharmacyGCost[] = [
  {
    id: 1,
    name: "Red Dot Pharmacy",
    domain: "reddot.pharma-platform.com",
    webAppUrl: "reddot.pharma-platform.com/app",
    databaseInfo: "Cloud SQL (PostgreSQL), Encrypted",
    mau: "12.5k",
    dailyApiCalls: 1250,
    totalApiCalls: 37500,
    tokenUsage: "12.4M",
    hostingCost: 15.20,
    servingCost: 24.50,
    storageCost: 5.10,
    totalCost: 44.80,
    status: 'Normal'
  },
  {
    id: 2,
    name: "Al Shifa Pharmacy",
    domain: "alshifa.pharma-platform.com",
    webAppUrl: "alshifa.pharma-platform.com/app",
    databaseInfo: "Google Spanner, High Availability",
    mau: "8.2k",
    dailyApiCalls: 650,
    totalApiCalls: 19500,
    tokenUsage: "6.8M",
    hostingCost: 12.00,
    servingCost: 14.20,
    storageCost: 3.50,
    totalCost: 29.70,
    status: 'Low Usage'
  },
  {
    id: 3,
    name: "Prime Pharmacy",
    domain: "prime.pharma-platform.com",
    webAppUrl: "prime.pharma-platform.com/app",
    databaseInfo: "Cloud SQL, Dedicated Instance",
    mau: "22k",
    dailyApiCalls: 2800,
    totalApiCalls: 84000,
    tokenUsage: "42.1M",
    hostingCost: 45.00,
    servingCost: 68.40,
    storageCost: 12.80,
    totalCost: 126.20,
    status: 'High Usage'
  }
];