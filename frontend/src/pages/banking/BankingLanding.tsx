import { useEffect, useRef, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowRight, Shield, TrendingUp, Users, Star,
  Info, X, ChevronRight, Eye, EyeOff, MessageCircle, Bot,
  Search, Phone, Mail, MapPin, Calendar,
  Clock, Send, Award, Globe2, User, LogOut, Bell, Bookmark, Settings, Check,
  BarChart2, AlertCircle,
} from 'lucide-react';

// ─── Cookie helpers ───────────────────────────────────────────────────────────
function getCookie(name: string): string | null {
  const m = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
  return m ? decodeURIComponent(m[1]) : null;
}
function setCookie(name: string, value: string, days: number) {
  const exp = new Date(Date.now() + days * 864e5).toUTCString();
  document.cookie = `${name}=${encodeURIComponent(value)}; expires=${exp}; path=/; SameSite=Lax`;
}
function generateUUID(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}
function getUTMParams() {
  const p = new URLSearchParams(window.location.search);
  const src = p.get('utm_source') || '';
  const MAP: Record<string, string> = {
    email: 'email', sms: 'sms', inapp: 'in_app', in_app: 'in_app',
    direct_mail: 'direct_mail', branch: 'branch',
  };
  return { referrer_channel: MAP[src.toLowerCase()] || 'web', utm_campaign: p.get('utm_campaign') };
}
function getDevice() {
  return /Mobi|Android/i.test(navigator.userAgent) ? 'mobile'
    : /iPad|Tablet/i.test(navigator.userAgent) ? 'tablet' : 'desktop';
}

// ─── Types ────────────────────────────────────────────────────────────────────
interface Product {
  product_id: string;
  product_name: string;
  category: string;
  subcategory: string;
  annual_fee: number;
  monthly_fee: number;
  min_balance: number;
  interest_rate: number;
  description: string;
  rewards_type: string;
  cash_back_pct: number;
  regular_apr_pct: number;
  avg_rating: number;
  min_credit_score: number;
  min_income: number;
  fee_waiver_condition: string;
  credit_tier_required?: string;
}
interface HeroContent { headline: string; subhead: string; cta_label: string; }
interface PersonalizeResponse {
  personalized: boolean; persona: string | null;
  first_name?: string | null;
  hero: HeroContent; product_cards: Product[];
}
interface PendingEvent {
  visitor_id: string; session_id: string;
  product_id?: string; product_category?: string;
  interaction_type: string; dwell_time: number;
}

// ─── Interaction batch ────────────────────────────────────────────────────────
const _pending: PendingEvent[] = [];
let _batchTimer: ReturnType<typeof setTimeout> | null = null;
function queueEvent(ev: PendingEvent) {
  _pending.push(ev);
  if (!_batchTimer) _batchTimer = setTimeout(flushEvents, 5000);
}
async function flushEvents() {
  _batchTimer = null;
  const batch = _pending.splice(0);
  for (const ev of batch) {
    try {
      await fetch('/api/landing/track', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(ev),
      });
    } catch { /* best-effort, never block UX */ }
  }
}

// ─── Display helpers ──────────────────────────────────────────────────────────
const SUBCAT_ICONS: Record<string, string> = {
  Checking: '💳', Savings: '💰', CD: '🔐', Credit: '💳',
  Auto: '🚗', Mortgage: '🏠', 'Home Equity': '🏠', HELOC: '🏡',
  Investment: '📈', 'Personal Loan': '💼', 'Business Loan': '🏢',
  'Agricultural Loan': '🌾',
};
const APR_SUBCATS = new Set(['Credit', 'Auto', 'Mortgage', 'Home Equity', 'HELOC',
  'Personal Loan', 'Business Loan', 'Agricultural Loan']);

// Color-coded subcategory badge styles
const SUBCAT_COLORS: Record<string, string> = {
  Checking: 'bg-cyan-100 text-cyan-700',
  Savings: 'bg-emerald-100 text-emerald-700',
  CD: 'bg-blue-100 text-blue-700',
  Credit: 'bg-purple-100 text-purple-700',
  Auto: 'bg-orange-100 text-orange-700',
  Mortgage: 'bg-amber-100 text-amber-800',
  'Home Equity': 'bg-amber-100 text-amber-800',
  HELOC: 'bg-yellow-100 text-yellow-800',
  Investment: 'bg-indigo-100 text-indigo-700',
  'Personal Loan': 'bg-violet-100 text-violet-700',
  'Business Loan': 'bg-sky-100 text-sky-700',
  'Agricultural Loan': 'bg-lime-100 text-lime-800',
};

function rateLabel(p: Product): string {
  if (p.cash_back_pct > 0) return `${p.cash_back_pct}% cash back`;
  if (p.interest_rate > 0) {
    const pct = (p.interest_rate * 100).toFixed(2);
    return APR_SUBCATS.has(p.subcategory) ? `From ${pct}% APR` : `${pct}% APY`;
  }
  if (p.regular_apr_pct > 0) return `${p.regular_apr_pct}% APR`;
  return '';
}

// Rate text color: APY = emerald, APR loans = orange, cash back = violet
function rateColor(p: Product): string {
  if (p.cash_back_pct > 0) return 'text-violet-600';
  if (APR_SUBCATS.has(p.subcategory)) return 'text-orange-600';
  return 'text-emerald-600';
}

// ─── Filter configuration ─────────────────────────────────────────────────────
const PERSONAL_CHIPS = ['All', 'Checking', 'Savings', 'CDs', 'Credit Cards', 'Loans', 'Mortgage', 'Investment'];
const BUSINESS_CHIPS = ['All', 'Checking', 'Savings', 'Business Loans', 'Cards'];
const CHIP_SUBCATS: Record<string, string[]> = {
  Checking: ['Checking'], Savings: ['Savings'], CDs: ['CD'],
  'Credit Cards': ['Credit'], Loans: ['Auto', 'Personal Loan', 'Home Equity', 'HELOC'],
  Mortgage: ['Mortgage'], Investment: ['Investment'],
  'Business Loans': ['Business Loan'], Cards: ['Credit'],
};

// ─── Persona hero copy ────────────────────────────────────────────────────────
const PERSONA_HERO: Record<string, HeroContent> = {
  'Wealth Builder': {
    headline: "Your home's equity could work harder for you.",
    subhead: "Unlock flexible financing backed by the value you've already built.",
    cta_label: 'Find My Best Rate',
  },
  'Retiree Anchor': {
    headline: "Lock in today's high rates before they change.",
    subhead: 'Earn more on every dollar with FDIC-insured CDs and money market accounts.',
    cta_label: "See Today's Rates",
  },
  'Digital Native': {
    headline: 'Every swipe earns. Every dollar rewarded.',
    subhead: 'Premium cash back, no annual fee, and instant mobile control.',
    cta_label: 'Get My Card',
  },
  'Everyday Essential': {
    headline: 'Simple, fee-free banking the way it should be.',
    subhead: 'No minimums, no surprises  -  just a checking account that works for you.',
    cta_label: 'Open an Account',
  },
  'At-Risk Saver': {
    headline: 'Start fresh. Banking without the hidden costs.',
    subhead: 'A no-fee account to get back on track  -  with tools to help you save.',
    cta_label: 'Get Started Free',
  },
};
const DEFAULT_HERO: HeroContent = {
  headline: 'Banking that puts you first.',
  subhead: 'Personalized financial solutions for every stage of life.',
  cta_label: 'Explore Products',
};

// ─── Chatbot ──────────────────────────────────────────────────────────────────

interface ChatOption { label: string; value: string; }
interface ChatMessage {
  id: string; type: 'bot' | 'user' | 'products';
  text?: string; products?: Product[];
}

const CHAT_QUESTIONS: { id: string; question: string; options: ChatOption[] }[] = [
  {
    id: 'age',
    question: "Hi! I'm your Meridian guide 👋  Let's find the right products for you.\n\nWhich age group are you in?",
    options: [
      { label: '18 – 25', value: '18-25' },
      { label: '26 – 35', value: '26-35' },
      { label: '36 – 50', value: '36-50' },
      { label: '51 – 65', value: '51-65' },
      { label: '65+',     value: '65+'   },
    ],
  },
  {
    id: 'goal',
    question: "What's your main financial goal right now?",
    options: [
      { label: 'Save more money',      value: 'save'     },
      { label: 'Build or fix credit',  value: 'credit'   },
      { label: 'Buy a home',           value: 'home'     },
      { label: 'Plan for retirement',  value: 'retire'   },
      { label: 'Grow my business',     value: 'business' },
    ],
  },
  {
    id: 'income',
    question: 'What is your approximate monthly income?',
    options: [
      { label: 'Under $2,000',      value: 'low'   },
      { label: '$2,000 – $5,000',   value: 'mid'   },
      { label: '$5,000 – $10,000',  value: 'high'  },
      { label: 'Over $10,000',      value: 'vhigh' },
    ],
  },
  {
    id: 'home_status',
    question: 'Do you currently own a home?',
    options: [
      { label: 'Yes, I own a home',     value: 'own'    },
      { label: 'No, I rent',            value: 'rent'   },
      { label: 'Planning to buy soon',  value: 'buying' },
    ],
  },
  {
    id: 'priority',
    question: 'Almost done! What matters most to you in a banking product?',
    options: [
      { label: 'No fees',              value: 'no_fees' },
      { label: 'High returns / rates', value: 'returns' },
      { label: 'Rewards & cash back',  value: 'rewards' },
      { label: 'Easy mobile access',   value: 'digital' },
    ],
  },
];

function scoreProductsFromChat(products: Product[], answers: Record<string, string>): Product[] {
  const { age, goal, income, home_status, priority } = answers;
  const scored = products.map(p => {
    let score = 0;
    const sub = p.subcategory;
    const cat = p.category;

    // Age
    if (age === '18-25' && ['Credit', 'Checking'].includes(sub))                      score += 3;
    if (age === '26-35' && ['Checking', 'Savings', 'Mortgage', 'Auto'].includes(sub)) score += 2;
    if (age === '36-50' && ['Mortgage', 'Investment', 'Home Equity', 'HELOC'].includes(sub)) score += 3;
    if ((age === '51-65' || age === '65+') && ['CD', 'Savings', 'Investment'].includes(sub)) score += 4;

    // Goal
    if (goal === 'save'     && ['Savings', 'CD'].includes(sub))                  score += 4;
    if (goal === 'credit'   && sub === 'Credit')                                  score += 5;
    if (goal === 'credit'   && p.product_name.toLowerCase().includes('secured'))  score += 2;
    if (goal === 'home' && home_status !== 'own'  && sub === 'Mortgage')                     score += 5; // buying/renting → mortgage
    if (goal === 'home' && home_status === 'own'  && ['Home Equity', 'HELOC'].includes(sub)) score += 3; // already owns → equity (handled above too)
    if (goal === 'retire'   && sub === 'Investment')                              score += 5;
    if (goal === 'retire'   && sub === 'CD')                                      score += 3;
    if (goal === 'business' && cat === 'Business')                                score += 5;

    // Income  -  penalise products above affordability threshold
    if (income === 'low'  && p.min_income > 20000) score -= 5;
    if (income === 'mid'  && p.min_income > 50000) score -= 5;
    if (income === 'high' && p.min_income > 100000) score -= 5;

    // Home ownership  -  owning a home doesn't imply wanting equity products;
    // only boost them when the goal is explicitly home-related.
    // Renters are ineligible for equity products and shouldn't need mortgages yet.
    if (home_status === 'own'    && goal === 'home' && ['Home Equity', 'HELOC'].includes(sub)) score += 6;
    if (home_status === 'own'    && sub === 'Mortgage')                                         score -= 3; // already has one
    if (home_status === 'buying' && sub === 'Mortgage')                                         score += 6;
    if (home_status === 'rent'   && ['Home Equity', 'HELOC'].includes(sub))                     score -= 10; // ineligible
    if (home_status === 'rent'   && sub === 'Mortgage')                                         score -= 2;

    // Priority
    if (priority === 'no_fees'  && p.annual_fee === 0 && p.monthly_fee === 0) score += 3;
    if (priority === 'returns'  && p.interest_rate > 0.02)                   score += 3;
    if (priority === 'rewards'  && p.rewards_type !== 'none')                 score += 4;
    if (priority === 'digital'  && ['Credit', 'Checking'].includes(sub))      score += 2;

    // Boost well-rated products slightly
    score += (p.avg_rating - 4) * 0.5;

    return { product: p, score };
  });
  return scored
    .filter(s => s.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 3)
    .map(s => s.product);
}

// ─── Fallback: all 28 products (used if /api/banking/products is unreachable) ─
const FALLBACK: Product[] = [
  // Personal  -  Checking
  { product_id: 'MRD_P001', product_name: 'Meridian Essential Checking', category: 'Personal', subcategory: 'Checking', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0, description: 'No-fee everyday checking with free mobile deposit, Bill Pay, and Zelle. No minimum balance required.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.4, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P002', product_name: 'Meridian Plus Checking', category: 'Personal', subcategory: 'Checking', annual_fee: 0, monthly_fee: 12, min_balance: 0, interest_rate: 0.0005, description: 'Full-featured checking with 0.05% APY on your balance. Monthly fee waived with $500+ direct deposit.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.2, min_credit_score: 0, min_income: 20000, fee_waiver_condition: 'direct_deposit_500' },
  { product_id: 'MRD_P003', product_name: 'Meridian Prestige Checking', category: 'Personal', subcategory: 'Checking', annual_fee: 0, monthly_fee: 25, min_balance: 2500, interest_rate: 0.001, description: 'Premium checking with 0.10% APY, unlimited ATM fee rebates, and a dedicated relationship banker. Waived with $2,500 daily balance.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.5, min_credit_score: 0, min_income: 50000, fee_waiver_condition: 'balance_2500' },
  // Personal  -  Savings
  { product_id: 'MRD_P004', product_name: 'Meridian Basic Savings', category: 'Personal', subcategory: 'Savings', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.008, description: 'Simple savings account with 0.80% APY. No monthly fee, no minimum balance. FDIC insured.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.1, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P005', product_name: 'Meridian High-Yield Savings', category: 'Personal', subcategory: 'Savings', annual_fee: 0, monthly_fee: 0, min_balance: 1000, interest_rate: 0.045, description: 'Earn 4.50% APY on every dollar above $1,000. No monthly fee. Automatic transfers from checking available.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.6, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P006', product_name: 'Meridian Money Market', category: 'Personal', subcategory: 'Savings', annual_fee: 0, monthly_fee: 0, min_balance: 5000, interest_rate: 0.0475, description: '4.75% APY money market account with check-writing privileges. Tiered rates reward higher balances. $5,000 minimum.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.5, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'balance_5000' },
  // Personal  -  CDs
  { product_id: 'MRD_P007', product_name: 'Meridian 12-Month CD', category: 'Personal', subcategory: 'CD', annual_fee: 0, monthly_fee: 0, min_balance: 500, interest_rate: 0.05, description: 'Lock in 5.00% APY for 12 months. FDIC insured up to $250,000. Penalty for early withdrawal.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.4, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P008', product_name: 'Meridian 24-Month CD', category: 'Personal', subcategory: 'CD', annual_fee: 0, monthly_fee: 0, min_balance: 500, interest_rate: 0.0485, description: '4.85% APY for a 24-month term. Great for medium-term goals. Early withdrawal penalty of 180 days interest.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.3, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'none' },
  // Personal  -  Credit
  { product_id: 'MRD_P009', product_name: 'Meridian Cash Back Card', category: 'Personal', subcategory: 'Credit', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0, description: 'Unlimited 1.5% cash back on every purchase. 3% on groceries and gas. No annual fee. No rotating categories.', rewards_type: 'cash_back', cash_back_pct: 1.5, regular_apr_pct: 20.99, avg_rating: 4.6, min_credit_score: 670, min_income: 30000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P010', product_name: 'Meridian Rewards Visa', category: 'Personal', subcategory: 'Credit', annual_fee: 95, monthly_fee: 0, min_balance: 0, interest_rate: 0, description: '3x points on dining and travel, 2x on gas. 60,000 bonus points after $3,000 spend in first 3 months. $50 annual dining credit.', rewards_type: 'travel_points', cash_back_pct: 0, regular_apr_pct: 21.49, avg_rating: 4.7, min_credit_score: 700, min_income: 50000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P011', product_name: 'Meridian Platinum Card', category: 'Personal', subcategory: 'Credit', annual_fee: 195, monthly_fee: 0, min_balance: 0, interest_rate: 0, description: '4x points on travel booked through Meridian. Priority Pass airport lounge access. $200 annual travel credit. Concierge service.', rewards_type: 'travel_points', cash_back_pct: 0, regular_apr_pct: 22.49, avg_rating: 4.8, min_credit_score: 740, min_income: 75000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P012', product_name: 'Meridian Secured Card', category: 'Personal', subcategory: 'Credit', annual_fee: 35, monthly_fee: 0, min_balance: 300, interest_rate: 0, description: 'Build or rebuild your credit with a secured card. $300–$3,000 credit limit. Reports to all three major bureaus monthly.', rewards_type: 'cash_back', cash_back_pct: 1.0, regular_apr_pct: 24.99, avg_rating: 4.2, min_credit_score: 300, min_income: 12000, fee_waiver_condition: 'none' },
  // Personal  -  Loans
  { product_id: 'MRD_P013', product_name: 'Meridian Auto Loan', category: 'Personal', subcategory: 'Auto', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.0649, description: 'Finance your new or used vehicle at competitive rates. Terms from 36 to 84 months. Rate discount with auto-pay.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.3, min_credit_score: 580, min_income: 25000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P014', product_name: 'Meridian Personal Loan', category: 'Personal', subcategory: 'Personal Loan', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.0899, description: 'Unsecured personal loan from $5,000 to $50,000. Fixed rate, fixed term. Fund debt consolidation, home improvement, or major purchases.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.2, min_credit_score: 620, min_income: 30000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P015', product_name: 'Meridian Home Equity Loan', category: 'Personal', subcategory: 'Home Equity', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.0725, description: 'Fixed-rate home equity loan from $25,000 to $250,000. Up to 85% LTV. 10 to 20-year terms. Tax-deductible interest may apply.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.4, min_credit_score: 660, min_income: 45000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P016', product_name: 'Meridian HELOC', category: 'Personal', subcategory: 'HELOC', annual_fee: 50, monthly_fee: 0, min_balance: 0, interest_rate: 0.085, description: 'Variable-rate line of credit secured by your home. Draw period 10 years, repayment 20 years. Interest-only payments during draw.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.3, min_credit_score: 660, min_income: 45000, fee_waiver_condition: 'none' },
  // Personal  -  Mortgage
  { product_id: 'MRD_P017', product_name: 'Meridian 30yr Fixed Mortgage', category: 'Personal', subcategory: 'Mortgage', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.0675, description: '30-year fixed mortgage with competitive rates. Conventional loans up to $766,550. 20% down avoids PMI. Online application, local servicing.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.5, min_credit_score: 640, min_income: 40000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_P018', product_name: 'Meridian FHA Mortgage', category: 'Personal', subcategory: 'Mortgage', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.065, description: 'FHA loan with as little as 3.5% down. Credit scores as low as 580 accepted. Ideal for first-time homebuyers.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.4, min_credit_score: 580, min_income: 30000, fee_waiver_condition: 'none' },
  // Personal  -  Investment
  { product_id: 'MRD_P019', product_name: 'Meridian Traditional IRA', category: 'Personal', subcategory: 'Investment', annual_fee: 25, monthly_fee: 0, min_balance: 0, interest_rate: 0, description: 'Tax-deferred retirement savings. Contribute up to $7,000/year ($8,000 if 50+). Access to mutual funds, ETFs, and bonds.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.5, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'balance_5000' },
  { product_id: 'MRD_P020', product_name: 'Meridian Roth IRA', category: 'Personal', subcategory: 'Investment', annual_fee: 25, monthly_fee: 0, min_balance: 0, interest_rate: 0, description: 'Tax-free growth and withdrawals in retirement. Contribute after-tax dollars up to $7,000/year. No required minimum distributions.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.6, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'balance_5000' },
  // Business
  { product_id: 'MRD_B001', product_name: 'Meridian Business Essential Checking', category: 'Business', subcategory: 'Checking', annual_fee: 0, monthly_fee: 15, min_balance: 0, interest_rate: 0, description: 'Business checking with 200 free transactions/month. ACH, wire, and online bill pay included. Waived with $1,500 average balance.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.2, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'balance_1500' },
  { product_id: 'MRD_B002', product_name: 'Meridian Business Plus Checking', category: 'Business', subcategory: 'Checking', annual_fee: 0, monthly_fee: 30, min_balance: 0, interest_rate: 0.0002, description: 'Unlimited transactions, 0.02% APY on balances, dedicated business banker, and cash management tools.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.3, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'balance_5000' },
  { product_id: 'MRD_B003', product_name: 'Meridian Business Savings', category: 'Business', subcategory: 'Savings', annual_fee: 0, monthly_fee: 0, min_balance: 500, interest_rate: 0.035, description: '3.50% APY business savings. Separate your operating and reserve funds. Up to 6 withdrawals per month.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.3, min_credit_score: 0, min_income: 0, fee_waiver_condition: 'none' },
  { product_id: 'MRD_B004', product_name: 'Meridian Business Line of Credit', category: 'Business', subcategory: 'Business Loan', annual_fee: 150, monthly_fee: 0, min_balance: 0, interest_rate: 0.0799, description: 'Revolving line of credit $25K–$500K. Draw as needed, pay interest only on what you use. Annual review.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.4, min_credit_score: 660, min_income: 75000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_B005', product_name: 'Meridian Business Rewards Card', category: 'Business', subcategory: 'Credit', annual_fee: 95, monthly_fee: 0, min_balance: 0, interest_rate: 0, description: '3x points on business travel and software subscriptions, 2x on office supplies and dining. $500 welcome bonus after $3,000 spend.', rewards_type: 'travel_points', cash_back_pct: 0, regular_apr_pct: 21.99, avg_rating: 4.5, min_credit_score: 680, min_income: 50000, fee_waiver_condition: 'none' },
  // Agricultural
  { product_id: 'MRD_A001', product_name: 'Meridian Farm Operating Line', category: 'Agricultural', subcategory: 'Agricultural Loan', annual_fee: 100, monthly_fee: 0, min_balance: 0, interest_rate: 0.0725, description: 'Seasonal operating line of credit for crops, livestock, and equipment. $50K–$2M. Annual review with experienced agricultural lenders.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.4, min_credit_score: 600, min_income: 30000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_A002', product_name: 'Meridian Equipment Term Loan', category: 'Agricultural', subcategory: 'Agricultural Loan', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.0699, description: 'Finance tractors, combines, irrigation systems, and farm equipment. Terms up to 7 years. Up to 100% financing on new equipment.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.5, min_credit_score: 580, min_income: 25000, fee_waiver_condition: 'none' },
  { product_id: 'MRD_A003', product_name: 'Meridian Land Improvement Loan', category: 'Agricultural', subcategory: 'Agricultural Loan', annual_fee: 0, monthly_fee: 0, min_balance: 0, interest_rate: 0.0675, description: 'Fund drainage, irrigation, storage facilities, and soil improvements. Terms up to 15 years. Low rates for FSA-guaranteed borrowers.', rewards_type: 'none', cash_back_pct: 0, regular_apr_pct: 0, avg_rating: 4.4, min_credit_score: 580, min_income: 20000, fee_waiver_condition: 'none' },
];

// ─── News data ────────────────────────────────────────────────────────────────
interface NewsArticle {
  id: string; category: string; date: string; title: string;
  excerpt: string; readMin: number; featured?: boolean;
}
const NEWS_ARTICLES: NewsArticle[] = [
  { id: 'n1', category: 'Earnings', date: 'Jul 1, 2026', title: 'Meridian Bank Reports Record Q2 2026 Net Income of $142M', excerpt: 'Strong loan growth and disciplined expense management drove a 17% year-over-year increase in net income, with total assets reaching $13.4B. Our agricultural portfolio delivered exceptional performance amid continued commodity strength.', readMin: 4, featured: true },
  { id: 'n2', category: 'Product', date: 'Jun 24, 2026', title: 'Introducing Meridian One: A New Era of Mobile-First Banking', excerpt: 'Our redesigned mobile app brings instant account opening, real-time spending insights, and AI-powered savings goals to all customers. Available now on iOS and Android with biometric login and instant card freeze.', readMin: 3 },
  { id: 'n3', category: 'Community', date: 'Jun 17, 2026', title: 'Meridian Commits $50M to Rural Housing Initiative', excerpt: 'In partnership with state housing authorities, Meridian Bank will fund affordable mortgage programs for low-to-moderate income families across 12 rural counties. Applications open August 1, 2026.', readMin: 3 },
  { id: 'n4', category: 'Rate Update', date: 'Jun 10, 2026', title: 'High-Yield Savings Rate Increased to 4.85% APY', excerpt: 'Following the latest Federal Reserve guidance, Meridian is raising rates on all Meridian Growth Savings and Platinum CD accounts effective immediately. Existing customers will automatically receive the higher rate.', readMin: 2 },
  { id: 'n5', category: 'Awards', date: 'May 28, 2026', title: 'Meridian Bank Named "Best Community Bank" by Bankrate 2026', excerpt: 'For the third consecutive year, Meridian has been recognized for outstanding customer service, competitive rates, and community investment. Our Net Promoter Score of 72 leads all banks in our peer group.', readMin: 2 },
  { id: 'n6', category: 'Technology', date: 'May 12, 2026', title: 'AI-Powered Fraud Detection Blocks $8.2M in Suspicious Activity', excerpt: 'Our new machine learning fraud prevention system, deployed in March, has already prevented thousands of unauthorized transactions. Customers can now also set custom spending alerts and geographic restrictions via the app.', readMin: 3 },
];

// ─── Contact data ─────────────────────────────────────────────────────────────
const BRANCHES = [
  { name: 'Main Office  -  Financial District', address: '123 Commerce Blvd, Suite 400', city: 'Springfield, IL 62701', phone: '(217) 555-0100', hours: 'Mon–Fri 8:30am–5:00pm' },
  { name: 'Westside Branch', address: '4500 West Oak Avenue', city: 'Springfield, IL 62704', phone: '(217) 555-0120', hours: 'Mon–Sat 9:00am–4:00pm' },
  { name: 'Agricultural Services Center', address: '8100 Rural Route 12', city: 'Lincoln, IL 62656', phone: '(217) 555-0140', hours: 'Mon–Fri 8:00am–4:30pm' },
];


// ─── Main component ───────────────────────────────────────────────────────────
export default function BankingLanding() {
  const navigate = useNavigate();

  // Visit / identity state
  const [visitorId, setVisitorId]         = useState('');
  const [sessionId, setSessionId]         = useState('');
  const [visitNumber, setVisitNumber]     = useState(1);
  const [personalized, setPersonalized]   = useState(false);
  const [persona, setPersona]             = useState<string | null>(null);
  const [firstName, setFirstName]         = useState<string | null>(null);
  const [userEmail, setUserEmail]         = useState<string | null>(null);
  const [showProfile, setShowProfile]     = useState(false);
  const profileRef                        = useRef<HTMLDivElement>(null);

  // Profile panels
  const [activePanel, setActivePanel]     = useState<'profile' | 'preferences' | 'saved' | 'notifications' | null>(null);
  const [editName, setEditName]           = useState('');
  const [editEmail, setEditEmail]         = useState('');
  const [editPhone, setEditPhone]         = useState('');
  const [editSaved, setEditSaved]         = useState(false);

  // Saved products (persisted in localStorage)
  const [savedProducts, setSavedProducts] = useState<Set<string>>(() => {
    try { return new Set<string>(JSON.parse(localStorage.getItem('mrd_saved') ?? '[]')); }
    catch { return new Set<string>(); }
  });

  // Notification preferences (persisted in localStorage)
  const [notifRates, setNotifRates]             = useState(() => localStorage.getItem('mrd_n_rates') !== 'false');
  const [notifProducts, setNotifProducts]       = useState(() => localStorage.getItem('mrd_n_products') !== 'false');
  const [notifOffers, setNotifOffers]           = useState(() => localStorage.getItem('mrd_n_offers') !== 'false');
  const [notifNewsletter, setNotifNewsletter]   = useState(() => localStorage.getItem('mrd_n_news') !== 'false');

  // Preferences  -  financial goals
  const [prefGoals, setPrefGoals]         = useState<string[]>(() => {
    try { return JSON.parse(localStorage.getItem('mrd_pref_goals') ?? '[]'); }
    catch { return []; }
  });
  const [hero, setHero]                   = useState<HeroContent>(DEFAULT_HERO);
  const [heroReady, setHeroReady]         = useState(false);
  const [personalizedCards, setPersonalizedCards] = useState<Product[]>([]);

  // Product detail modal
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [eligCreditScore, setEligCreditScore]   = useState(700);
  const [eligIncome, setEligIncome]             = useState(60000);
  const [applyDone, setApplyDone]               = useState(false);

  // Comparison tool
  const [compareList, setCompareList]       = useState<string[]>([]);
  const [showCompareTool, setShowCompareTool] = useState(false);

  // Product catalog state
  const [allProducts, setAllProducts]     = useState<Product[]>(FALLBACK);
  const [activeTab, setActiveTab]         = useState<'all' | 'Personal' | 'Business' | 'Agricultural'>('all');
  const [activeSubcat, setActiveSubcat]   = useState('All');

  // UI state
  const [showSignIn, setShowSignIn]       = useState(false);
  const [showWhyTip, setShowWhyTip]       = useState(false);
  const [showPwd, setShowPwd]             = useState(false);
  const [showRegPwd, setShowRegPwd]       = useState(false);

  // Search overlay
  const [showSearch, setShowSearch]       = useState(false);
  const [searchQuery, setSearchQuery]     = useState('');
  const searchInputRef                    = useRef<HTMLInputElement>(null);

  // (no side panels  -  news, contact are on-page sections)

  // Contact form (in-page section)
  const [ctxName, setCtxName]             = useState('');
  const [ctxEmail, setCtxEmail]           = useState('');
  const [ctxMsg, setCtxMsg]               = useState('');
  const [ctxSent, setCtxSent]             = useState(false);
  const [ctxSending, setCtxSending]       = useState(false);

  // Success toast after sign-in / registration
  const [authToast, setAuthToast]         = useState<{ type: 'register' | 'signin'; name: string } | null>(null);

  // Sign In modal  -  two-tab state
  const [modalTab, setModalTab]           = useState<'register' | 'signin'>('register');
  const [signEmail, setSignEmail]         = useState('');
  const [signPwd, setSignPwd]             = useState('');
  const [signError, setSignError]         = useState('');
  const [signSubmitting, setSignSubmitting] = useState(false);

  // Registration form fields
  const [regName, setRegName]             = useState('');
  const [regEmail, setRegEmail]           = useState('');
  const [regPhone, setRegPhone]           = useState('');
  const [regPwd, setRegPwd]               = useState('');
  const [regConsent, setRegConsent]       = useState(false);
  const [regSubmitting, setRegSubmitting] = useState(false);
  const [regError, setRegError]           = useState('');

  // Chatbot state
  const [chatOpen, setChatOpen]       = useState(false);
  const [chatStep, setChatStep]       = useState(0);
  const [chatAnswers, setChatAnswers] = useState<Record<string, string>>({});
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
    { id: 'intro', type: 'bot', text: CHAT_QUESTIONS[0].question },
  ]);
  const [chatDone, setChatDone]       = useState(false);
  const [chatInput, setChatInput]     = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const chatEndRef   = useRef<HTMLDivElement>(null);
  const chatInputRef = useRef<HTMLInputElement>(null);

  // Tracking refs
  const cardRefs   = useRef<Map<string, HTMLDivElement>>(new Map());
  const dwellStart = useRef<Map<string, number>>(new Map());

  // ── 1. Visit registration + personalization ─────────────────────────────
  useEffect(() => {
    (async () => {
      let vid = getCookie('mrd_visitor_id');
      if (!vid) { vid = generateUUID(); setCookie('mrd_visitor_id', vid, 30); }
      setVisitorId(vid);
      const { referrer_channel, utm_campaign } = getUTMParams();
      try {
        const vRes = await fetch('/api/landing/visit', {
          method: 'POST', headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ visitor_id: vid, referrer_channel, utm_campaign, device_type: getDevice() }),
        });
        const vData = await vRes.json();
        setSessionId(vData.session_id);
        setVisitNumber(vData.visit_number);
        if (vData.personalized && vData.visit_number >= 2) {
          const pRes = await fetch(`/api/landing/personalize/${vid}`);
          const pr: PersonalizeResponse = await pRes.json();
          if (pr.personalized && pr.hero) {
            setPersona(pr.persona);
            setHero(PERSONA_HERO[pr.persona ?? ''] ?? pr.hero);
            setPersonalizedCards(pr.product_cards ?? []);
            setPersonalized(true);
            if (pr.first_name) setFirstName(pr.first_name);
            setModalTab('signin'); // returning visitor  -  default to Sign In tab
          }
        }
      } catch { /* silently fall back */ }
      setHeroReady(true);
    })();
    window.addEventListener('beforeunload', flushEvents);
    return () => window.removeEventListener('beforeunload', flushEvents);
  }, []);

  // ── Keyboard shortcuts (Escape closes overlays) ─────────────────────────
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        if (showSearch) { setShowSearch(false); return; }
        if (showSignIn) { setShowSignIn(false); }
      }
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        openSearch();
      }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [showSearch, showSignIn]);

  // ── 2. Load full product catalog ────────────────────────────────────────
  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/banking/products');
        if (!res.ok) return;
        const raw = await res.json();
        const prods: Product[] = Array.isArray(raw) ? raw : (raw.products ?? raw.data ?? []);
        if (prods.length > 0) setAllProducts(prods);
      } catch { /* keep fallback */ }
    })();
  }, []);

  // ── 3. IntersectionObserver for dwell tracking ──────────────────────────
  const handleIO = useCallback((pid: string, entering: boolean) => {
    if (!visitorId || !sessionId) return;
    const product = allProducts.find(p => p.product_id === pid);
    if (!product) return;
    if (entering) {
      dwellStart.current.set(pid, Date.now());
      queueEvent({ visitor_id: visitorId, session_id: sessionId, product_id: pid, product_category: product.subcategory, interaction_type: 'card_view', dwell_time: 0 });
    } else {
      const t = dwellStart.current.get(pid);
      if (t) {
        dwellStart.current.delete(pid);
        const dwell = Date.now() - t;
        if (dwell > 400) queueEvent({ visitor_id: visitorId, session_id: sessionId, product_id: pid, product_category: product.subcategory, interaction_type: 'card_view', dwell_time: dwell });
      }
    }
  }, [visitorId, sessionId, allProducts]);

  useEffect(() => {
    if (!visitorId || !sessionId) return;
    const obs = new IntersectionObserver(entries => {
      entries.forEach(e => {
        const pid = (e.target as HTMLElement).dataset.pid;
        if (pid) handleIO(pid, e.isIntersecting);
      });
    }, { threshold: 0.4 });
    cardRefs.current.forEach(el => obs.observe(el));
    return () => obs.disconnect();
  }, [visitorId, sessionId, allProducts, handleIO]);

  // ── Helpers ──────────────────────────────────────────────────────────────
  const onCardClick = (product: Product) => {
    if (!visitorId || !sessionId) return;
    queueEvent({ visitor_id: visitorId, session_id: sessionId, product_id: product.product_id, product_category: product.subcategory, interaction_type: 'card_click', dwell_time: 0 });
    void flushEvents();
  };

  const onCTA = () => {
    if (visitorId && sessionId) {
      queueEvent({ visitor_id: visitorId, session_id: sessionId, interaction_type: 'cta_click', dwell_time: 0 });
      void flushEvents();
    }
    document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' });
  };

  const countCat = (cat: string) => allProducts.filter(p => p.category === cat).length;

  // Search results
  const searchResults = searchQuery.trim().length > 1
    ? allProducts.filter(p => {
        const q = searchQuery.toLowerCase();
        return (
          p.product_name.toLowerCase().includes(q) ||
          p.subcategory.toLowerCase().includes(q) ||
          p.category.toLowerCase().includes(q) ||
          p.description.toLowerCase().includes(q)
        );
      })
    : [];

  // Contact form submit
  const handleContactSend = async () => {
    if (!ctxName.trim() || !ctxEmail.trim() || !ctxMsg.trim()) return;
    setCtxSending(true);
    await new Promise(r => setTimeout(r, 1200)); // simulate network
    setCtxSent(true);
    setCtxSending(false);
  };

  // Open search with focus
  const openSearch = () => {
    setShowSearch(true);
    setSearchQuery('');
    setTimeout(() => searchInputRef.current?.focus(), 80);
  };

  // ── Chatbot answer handler ────────────────────────────────────────────────
  const handleChatAnswer = (questionId: string, option: ChatOption) => {
    const newAnswers = { ...chatAnswers, [questionId]: option.value };
    setChatAnswers(newAnswers);

    // Track the answer
    if (visitorId && sessionId) {
      queueEvent({ visitor_id: visitorId, session_id: sessionId, interaction_type: 'chatbot_response', product_category: questionId, dwell_time: 0 });
    }

    const userMsg: ChatMessage = { id: `u-${questionId}`, type: 'user', text: option.label };
    const nextStep = chatStep + 1;

    if (nextStep < CHAT_QUESTIONS.length) {
      const nextQ = CHAT_QUESTIONS[nextStep];
      const botMsg: ChatMessage = { id: `b-${nextStep}`, type: 'bot', text: nextQ.question };
      setChatMessages(prev => [...prev, userMsg, botMsg]);
      setChatStep(nextStep);
    } else {
      // All questions answered  -  score products
      const recommended = scoreProductsFromChat(allProducts, newAnswers);
      const doneMsg: ChatMessage = { id: 'done', type: 'bot', text: recommended.length > 0 ? `Based on your answers, here are your top ${recommended.length} product matches:` : "Thanks! Explore our full catalog below to find what fits you best." };
      const productMsg: ChatMessage = { id: 'products', type: 'products', products: recommended };
      setChatMessages(prev => [...prev, userMsg, doneMsg, productMsg]);
      setChatDone(true);
      // Surface picks on the main page
      if (recommended.length > 0) setPersonalizedCards(recommended);
    }

    // Scroll to bottom
    setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
  };

  const resetChat = () => {
    setChatStep(0);
    setChatAnswers({});
    setChatMessages([{ id: 'intro', type: 'bot', text: CHAT_QUESTIONS[0].question }]);
    setChatDone(false);
    setChatInput('');
  };

  const handleSendMessage = async () => {
    const text = chatInput.trim();
    if (!text || chatLoading) return;
    setChatInput('');

    const userMsgId = `u-${Date.now()}`;
    setChatMessages(prev => [...prev, { id: userMsgId, type: 'user', text }]);
    setChatLoading(true);

    // Build a brief context string from recent messages (last 4)
    const recentContext = chatMessages
      .slice(-4)
      .filter(m => m.type === 'bot' || m.type === 'user')
      .map(m => (m.type === 'bot' ? `Bot: ${m.text}` : `Visitor: ${m.text}`))
      .join(' | ');

    try {
      const res = await fetch('/api/landing/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text, context: recentContext }),
      });
      const data = await res.json();
      const reply = data.reply || "I'm here to help with any banking questions!";
      setChatMessages(prev => [
        ...prev,
        { id: `b-${Date.now()}`, type: 'bot', text: reply },
      ]);
    } catch {
      setChatMessages(prev => [
        ...prev,
        {
          id: `b-${Date.now()}`,
          type: 'bot',
          text: "Sorry, I couldn't reach the server. Please try again in a moment!",
        },
      ]);
    } finally {
      setChatLoading(false);
      setTimeout(() => chatEndRef.current?.scrollIntoView({ behavior: 'smooth' }), 50);
      chatInputRef.current?.focus();
    }
  };

  // ── Filtered products for catalog ────────────────────────────────────────
  const filteredProducts = (() => {
    let base = activeTab === 'all' ? allProducts : allProducts.filter(p => p.category === activeTab);
    if (activeSubcat !== 'All' && CHIP_SUBCATS[activeSubcat]) {
      const allowed = CHIP_SUBCATS[activeSubcat];
      base = base.filter(p => allowed.includes(p.subcategory));
    }
    return base;
  })();

  const chips = activeTab === 'Personal' ? PERSONAL_CHIPS : activeTab === 'Business' ? BUSINESS_CHIPS : null;

  // ── Product card render helper (not a component  -  avoids nested component issues) ──
  const renderCard = (product: Product, recRank?: number) => {
    const rate  = rateLabel(product);
    const isRec = recRank === 0 && personalized;
    const isGood = recRank === 1 && personalized;
    const isRel  = recRank === 2 && personalized;
    return (
      <div
        key={product.product_id}
        ref={el => { if (el) { cardRefs.current.set(product.product_id, el); } else { cardRefs.current.delete(product.product_id); } }}
        data-pid={product.product_id}
        onClick={() => { onCardClick(product); openProductDetail(product); }}
        className={`group relative bg-white rounded-2xl border cursor-pointer transition-all duration-200 hover:shadow-xl hover:-translate-y-1 flex flex-col ${
          isRec ? 'border-emerald-400 shadow-lg ring-2 ring-emerald-100' : 'border-slate-200 hover:border-blue-300 hover:shadow-md'
        }`}
      >
        {isRec && (
          <div className="absolute -top-3 left-5">
            <span className="bg-emerald-500 text-white text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-md">
              <Star className="w-3 h-3 fill-white" /> Best Match
            </span>
          </div>
        )}
        <div className="p-5 flex-1 flex flex-col">
          <div className="flex items-start justify-between gap-2 mb-3">
            <span className="text-3xl leading-none">{SUBCAT_ICONS[product.subcategory] ?? '🏦'}</span>
            <div className="flex flex-wrap gap-1 justify-end">
              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SUBCAT_COLORS[product.subcategory] ?? 'bg-slate-100 text-slate-500'}`}>{product.subcategory}</span>
              {isGood && <span className="text-[10px] font-bold bg-blue-50 text-blue-700 px-2 py-0.5 rounded-full">Good Fit</span>}
              {isRel  && <span className="text-[10px] font-bold bg-fuchsia-50 text-fuchsia-700 px-2 py-0.5 rounded-full">Relevant</span>}
            </div>
          </div>

          <h3 className="font-bold text-[#0F2744] text-sm leading-snug mb-1.5" style={{ fontFamily: "'Inter', sans-serif" }}>{product.product_name}</h3>

          {rate && (
            <p className={`font-extrabold text-xl mb-2 leading-none ${rateColor(product)}`}>
              {rate}
            </p>
          )}

          <p className="text-slate-500 text-xs leading-relaxed mb-4 flex-1">{product.description}</p>

          <div className="space-y-1.5 text-xs">
            {product.annual_fee === 0 && product.monthly_fee === 0 ? (
              <div className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                No fees
              </div>
            ) : (
              <>
                {product.annual_fee > 0 && (
                  <div className="flex items-center gap-1.5 text-slate-500">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300 flex-shrink-0" />
                    ${product.annual_fee}/yr annual fee
                  </div>
                )}
                {product.monthly_fee > 0 && (
                  <div className="flex items-center gap-1.5 text-slate-500">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-300 flex-shrink-0" />
                    ${product.monthly_fee}/mo
                    {product.fee_waiver_condition && product.fee_waiver_condition !== 'none' && (
                      <span className="text-emerald-600 ml-0.5">(waivable)</span>
                    )}
                  </div>
                )}
              </>
            )}
            {product.min_balance > 0 && (
              <div className="flex items-center gap-1.5 text-slate-500">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-300 flex-shrink-0" />
                Min balance: ${product.min_balance.toLocaleString()}
              </div>
            )}
            {product.min_credit_score > 0 && (
              <div className="flex items-center gap-1.5 text-slate-500">
                <span className="w-1.5 h-1.5 rounded-full bg-slate-300 flex-shrink-0" />
                Credit score: {product.min_credit_score}+
              </div>
            )}
          </div>
        </div>

        <div className="px-5 py-3 border-t border-slate-100 flex items-center justify-between mt-auto">
          <div className="flex items-center gap-1">
            <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
            <span className="text-xs font-bold text-slate-700">{product.avg_rating}</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={e => toggleSave(product.product_id, e)}
              title={savedProducts.has(product.product_id) ? 'Remove bookmark' : 'Save product'}
              className="p-1 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <Bookmark className={`w-4 h-4 transition-colors ${
                savedProducts.has(product.product_id)
                  ? 'text-amber-500 fill-amber-500'
                  : 'text-slate-300 hover:text-amber-400'
              }`} />
            </button>
            <button
              onClick={e => toggleCompare(product.product_id, e)}
              title={
                compareList.includes(product.product_id) ? 'Remove from compare'
                : compareList.length >= 3 ? 'Max 3 products'
                : 'Add to compare'
              }
              className={`p-1 rounded-lg transition-colors ${
                compareList.includes(product.product_id)
                  ? 'text-blue-600 bg-blue-50'
                  : compareList.length >= 3
                  ? 'text-slate-200 cursor-not-allowed'
                  : 'text-slate-300 hover:text-blue-500 hover:bg-slate-50'
              }`}
            >
              <BarChart2 className="w-4 h-4" />
            </button>
            <button
              onClick={e => { e.stopPropagation(); onCardClick(product); openProductDetail(product); }}
              className="flex items-center gap-1 text-xs font-semibold text-blue-700 hover:text-blue-900 transition-all"
            >
              Learn More <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </button>
          </div>
        </div>
      </div>
    );
  };

  // ── Profile dropdown click-outside ───────────────────────────────────────
  useEffect(() => {
    if (!showProfile) return;
    const handler = (e: MouseEvent) => {
      if (profileRef.current && !profileRef.current.contains(e.target as Node)) {
        setShowProfile(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showProfile]);

  // ── Logout ────────────────────────────────────────────────────────────────
  const handleLogout = () => {
    setFirstName(null);
    setUserEmail(null);
    setPersona(null);
    setPersonalized(false);
    setPersonalizedCards([]);
    setHero(DEFAULT_HERO);
    setShowProfile(false);
    setActivePanel(null);
    document.cookie = 'mrd_visitor_id=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT';
  };

  // ── Bookmark toggle ───────────────────────────────────────────────────────
  const toggleSave = (pid: string, e: React.MouseEvent) => {
    e.stopPropagation();
    setSavedProducts(prev => {
      const next = new Set(prev);
      if (next.has(pid)) next.delete(pid); else next.add(pid);
      localStorage.setItem('mrd_saved', JSON.stringify([...next]));
      return next;
    });
  };

  // ── Comparison tool ───────────────────────────────────────────────────────
  const toggleCompareById = (pid: string) => {
    setCompareList(prev => {
      if (prev.includes(pid)) return prev.filter(id => id !== pid);
      if (prev.length >= 3) return prev;
      return [...prev, pid];
    });
  };
  const toggleCompare = (pid: string, e: React.MouseEvent) => {
    e.stopPropagation();
    toggleCompareById(pid);
  };

  // ── Open product detail modal ─────────────────────────────────────────────
  const openProductDetail = (product: Product) => {
    setSelectedProduct(product);
    setApplyDone(false);
    setEligCreditScore(700);
    setEligIncome(60000);
  };

  // ── Open profile panel ────────────────────────────────────────────────────
  const openPanel = (panel: typeof activePanel) => {
    if (panel === 'profile') {
      setEditName(firstName ?? '');
      setEditEmail(userEmail ?? '');
      setEditPhone('');
      setEditSaved(false);
    }
    setActivePanel(panel);
    setShowProfile(false);
  };

  // ── Save profile edits ────────────────────────────────────────────────────
  const saveProfile = () => {
    if (editName.trim()) setFirstName(editName.trim());
    if (editEmail.trim()) setUserEmail(editEmail.trim());
    setEditSaved(true);
    setTimeout(() => setEditSaved(false), 2500);
  };

  // ── Toggle notification + persist ────────────────────────────────────────
  const toggleNotif = (key: string, val: boolean, setter: (v: boolean) => void) => {
    setter(val);
    localStorage.setItem(key, String(val));
  };

  // ── Save preferences ──────────────────────────────────────────────────────
  const savePreferences = (goals: string[]) => {
    setPrefGoals(goals);
    localStorage.setItem('mrd_pref_goals', JSON.stringify(goals));
  };

  // ── Registration submit handler ───────────────────────────────────────────
  const showAuthToast = (type: 'register' | 'signin', name: string) => {
    setAuthToast({ type, name });
    setTimeout(() => setAuthToast(null), 4500);
  };

  const handleRegister = async () => {
    setRegError('');
    if (!regName.trim()) { setRegError('Please enter your first name.'); return; }
    if (!regEmail.trim() || !regEmail.includes('@')) { setRegError('Please enter a valid email address.'); return; }
    if (regPwd.length < 6) { setRegError('Password must be at least 6 characters.'); return; }
    if (!regConsent) { setRegError('Please agree to receive personalized offers to continue.'); return; }
    setRegSubmitting(true);
    try {
      const res = await fetch('/api/landing/register', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          visitor_id: visitorId,
          first_name: regName.trim(),
          email: regEmail.trim(),
          phone: regPhone.trim() || null,
          consent: regConsent,
          password: regPwd,
        }),
      });
      const data = await res.json();
      if (!data.ok) { setRegError('Could not create your account. Please try again.'); return; }
      const name = regName.trim();
      setFirstName(name);
      setUserEmail(regEmail.trim());
      setPersonalized(true);
      setHero(PERSONA_HERO[persona ?? ''] ?? DEFAULT_HERO);
      setShowSignIn(false);
      showAuthToast('register', name);
    } catch {
      setRegError('Something went wrong. Please try again.');
    } finally {
      setRegSubmitting(false);
    }
  };

  // ── Sign-in submit handler ────────────────────────────────────────────────
  const handleSignIn = async () => {
    setSignError('');
    if (!signEmail.trim() || !signEmail.includes('@')) { setSignError('Please enter a valid email address.'); return; }
    if (!signPwd.trim()) { setSignError('Please enter your password.'); return; }
    setSignSubmitting(true);
    try {
      const res = await fetch('/api/landing/signin', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: signEmail.trim(), password: signPwd }),
      });
      const data = await res.json();
      if (!data.ok) {
        setSignError(data.error || 'Sign in failed. Please check your credentials.');
        return;
      }
      // Restore visitor identity and personalize
      setCookie('mrd_visitor_id', data.visitor_id, 30);
      setVisitorId(data.visitor_id);
      if (data.first_name) setFirstName(data.first_name);
      setUserEmail(signEmail.trim());
      if (data.persona) {
        setPersona(data.persona);
        setHero(PERSONA_HERO[data.persona] ?? DEFAULT_HERO);
      }
      setPersonalized(true);
      // Load personalized product recommendations for this user
      try {
        const pRes = await fetch(`/api/landing/personalize/${data.visitor_id}`);
        const pr = await pRes.json();
        if (pr.product_cards?.length) setPersonalizedCards(pr.product_cards);
      } catch { /* non-critical */ }
      setShowSignIn(false);
      showAuthToast('signin', data.first_name || 'there');
    } catch {
      setSignError('Something went wrong. Please try again.');
    } finally {
      setSignSubmitting(false);
    }
  };

  // ── Auth success toast ───────────────────────────────────────────────────
  const authToastEl = authToast && (
    <div className="fixed top-6 left-1/2 -translate-x-1/2 z-[60] animate-in fade-in slide-in-from-top-4 duration-300">
      <div className="bg-white rounded-2xl shadow-2xl border border-slate-100 px-6 py-5 flex items-start gap-4 min-w-[320px] max-w-sm">
        <div className={`w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 ${authToast.type === 'register' ? 'bg-emerald-100' : 'bg-blue-100'}`}>
          <svg className={`w-5 h-5 ${authToast.type === 'register' ? 'text-emerald-600' : 'text-blue-600'}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-bold text-slate-900 text-sm">
            {authToast.type === 'register' ? `Welcome to Meridian Bank, ${authToast.name}!` : `Welcome back, ${authToast.name}!`}
          </p>
          <p className="text-slate-500 text-xs mt-0.5 leading-relaxed">
            {authToast.type === 'register'
              ? 'Your account has been created. We\'ve personalized your product recommendations below.'
              : 'You\'re signed in. Your personalized experience has been restored.'}
          </p>
        </div>
        <button onClick={() => setAuthToast(null)} className="text-slate-300 hover:text-slate-500 flex-shrink-0 mt-0.5">
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );

  // ── Sign-in modal (two-tab) ───────────────────────────────────────────────
  const signInModal = showSignIn && (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={e => { if (e.target === e.currentTarget) setShowSignIn(false); }}
    >
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md mx-4 overflow-hidden">

        {/* Modal header */}
        <div className="bg-[#0F2744] px-6 py-4 flex items-center justify-between">
          <div>
            <span className="font-bold text-base">
              <span className="text-amber-300">Meridian</span>
              <span className="text-white"> Bank</span>
            </span>
            <div className="text-blue-300 text-[11px] tracking-wide">Online Banking</div>
          </div>
          <button onClick={() => setShowSignIn(false)} className="text-blue-300 hover:text-white transition-colors p-1">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-slate-200">
          <button
            onClick={() => { setModalTab('register'); setRegError(''); setSignError(''); }}
            className={`flex-1 py-3 text-sm font-bold transition-all border-b-2 ${
              modalTab === 'register'
                ? 'border-emerald-500 text-emerald-700 bg-emerald-50/50'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Create Account
          </button>
          <button
            onClick={() => { setModalTab('signin'); setRegError(''); setSignError(''); }}
            className={`flex-1 py-3 text-sm font-bold transition-all border-b-2 ${
              modalTab === 'signin'
                ? 'border-blue-600 text-blue-700 bg-blue-50/50'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            Sign In
          </button>
        </div>

        <div className="px-6 py-6">
          {/* ── Register tab ── */}
          {modalTab === 'register' && (
            <>
              <p className="text-slate-500 text-xs mb-5 leading-relaxed">
                Create your free Meridian Bank profile to get personalized product recommendations.
              </p>
              <div className="space-y-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-widest">First Name <span className="text-red-400">*</span></label>
                  <input
                    type="text" value={regName} onChange={e => setRegName(e.target.value)}
                    placeholder="e.g. Sarah"
                    className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-widest">Email Address <span className="text-red-400">*</span></label>
                  <input
                    type="email" value={regEmail} onChange={e => setRegEmail(e.target.value)}
                    placeholder="your@email.com"
                    className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-widest">Password <span className="text-red-400">*</span></label>
                  <div className="relative">
                    <input
                      type={showRegPwd ? 'text' : 'password'} value={regPwd} onChange={e => setRegPwd(e.target.value)}
                      placeholder="Min. 6 characters"
                      className="w-full border border-slate-200 rounded-xl px-4 py-2.5 pr-11 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition"
                    />
                    <button type="button" onClick={() => setShowRegPwd(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      {showRegPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-widest">Phone <span className="text-slate-400 normal-case font-normal">(optional)</span></label>
                  <input
                    type="tel" value={regPhone} onChange={e => setRegPhone(e.target.value)}
                    placeholder="+1 (555) 000-0000"
                    className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition"
                  />
                </div>
                <label className="flex items-start gap-3 cursor-pointer">
                  <input
                    type="checkbox" checked={regConsent} onChange={e => setRegConsent(e.target.checked)}
                    className="mt-0.5 w-4 h-4 accent-emerald-600 flex-shrink-0"
                  />
                  <span className="text-xs text-slate-500 leading-relaxed">
                    I agree to receive personalized product offers and rate alerts from Meridian Bank. You can unsubscribe at any time.
                  </span>
                </label>
              </div>
              {regError && (
                <div className="mt-3 flex items-start gap-2 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
                  <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <p className="text-red-600 text-xs">{regError}</p>
                </div>
              )}
              <button
                onClick={handleRegister}
                disabled={regSubmitting}
                className="w-full mt-5 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-50 text-white font-bold py-3.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 shadow-sm"
              >
                {regSubmitting
                  ? <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Creating account…</>
                  : <>Create My Account <ArrowRight className="w-4 h-4" /></>
                }
              </button>
              <p className="text-center text-xs text-slate-400 mt-3">
                Already have an account?{' '}
                <button onClick={() => { setModalTab('signin'); setRegError(''); }} className="text-blue-600 hover:underline font-medium">Sign in</button>
              </p>
            </>
          )}

          {/* ── Sign In tab ── */}
          {modalTab === 'signin' && (
            <>
              <p className="text-slate-500 text-xs mb-5 leading-relaxed">
                {firstName
                  ? `Welcome back, ${firstName}! Sign in to access your personalized dashboard.`
                  : 'Sign in to your Meridian Bank profile.'}
              </p>
              <div className="space-y-3.5">
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-widest">Email Address</label>
                  <input
                    type="email" value={signEmail} onChange={e => setSignEmail(e.target.value)}
                    onKeyDown={e => { if (e.key === 'Enter') handleSignIn(); }}
                    placeholder="your@email.com"
                    className="w-full border border-slate-200 rounded-xl px-4 py-2.5 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                  />
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-500 mb-1 uppercase tracking-widest">Password</label>
                  <div className="relative">
                    <input
                      type={showPwd ? 'text' : 'password'} value={signPwd} onChange={e => setSignPwd(e.target.value)}
                      onKeyDown={e => { if (e.key === 'Enter') handleSignIn(); }}
                      placeholder="••••••••"
                      className="w-full border border-slate-200 rounded-xl px-4 py-2.5 pr-11 text-sm text-slate-800 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition"
                    />
                    <button type="button" onClick={() => setShowPwd(v => !v)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                      {showPwd ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>
              </div>
              {signError && (
                <div className="mt-3 flex items-start gap-2 bg-red-50 border border-red-200 rounded-xl px-3 py-2">
                  <svg className="w-4 h-4 text-red-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                  <p className="text-red-600 text-xs">{signError}</p>
                </div>
              )}
              <button
                onClick={handleSignIn}
                disabled={signSubmitting}
                className="w-full mt-5 bg-[#0F2744] hover:bg-[#1a3a5c] disabled:opacity-50 text-white font-bold py-3.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-2 shadow-sm"
              >
                {signSubmitting
                  ? <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Signing in…</>
                  : <>Sign In <ArrowRight className="w-4 h-4" /></>
                }
              </button>
              <div className="relative my-4">
                <div className="absolute inset-0 flex items-center"><div className="w-full border-t border-slate-100" /></div>
                <div className="relative flex justify-center"><span className="bg-white px-3 text-xs text-slate-400 font-medium">or</span></div>
              </div>
              <button
                onClick={() => navigate('/banking')}
                className="w-full border-2 border-slate-200 text-slate-700 hover:bg-slate-50 font-semibold py-2.5 rounded-xl text-sm transition-colors"
              >
                Continue as Demo User →
              </button>
              <div className="flex justify-between text-xs text-blue-600 mt-4">
                <span />
                <button onClick={() => { setModalTab('register'); setSignError(''); }} className="hover:underline font-medium">Create an account</button>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-white" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>

      {authToastEl}
      {signInModal}

      {/* ══ Search overlay ══════════════════════════════════════════════════ */}
      {showSearch && (
        <div className="fixed inset-0 z-[55] bg-[#0a1a2e]/95 backdrop-blur-sm flex flex-col"
          onClick={e => { if (e.target === e.currentTarget) setShowSearch(false); }}>
          {/* Search bar */}
          <div className="max-w-2xl mx-auto w-full px-6 pt-16">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-blue-400" />
              <input
                ref={searchInputRef}
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Search products, rates, features…"
                className="w-full bg-[#1a3050] text-white placeholder-blue-400 border border-blue-700/50 rounded-2xl pl-12 pr-12 py-4 text-lg focus:outline-none focus:border-amber-400 transition"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="absolute right-4 top-1/2 -translate-y-1/2 text-blue-400 hover:text-white">
                  <X className="w-5 h-5" />
                </button>
              )}
            </div>
            <div className="flex items-center justify-between mt-3">
              <p className="text-blue-400 text-sm">
                {searchQuery.trim().length > 1
                  ? `${searchResults.length} result${searchResults.length !== 1 ? 's' : ''} for "${searchQuery}"`
                  : 'Type at least 2 characters to search'}
              </p>
              <button onClick={() => setShowSearch(false)} className="text-blue-400 hover:text-white text-sm flex items-center gap-1">
                <X className="w-4 h-4" /> Close
              </button>
            </div>
          </div>

          {/* Quick filter chips */}
          {!searchQuery && (
            <div className="max-w-2xl mx-auto w-full px-6 mt-6">
              <p className="text-blue-500 text-xs uppercase tracking-widest mb-3 font-semibold">Browse by category</p>
              <div className="flex flex-wrap gap-2">
                {['Checking', 'Savings', 'Credit', 'Mortgage', 'CD', 'Investment', 'Business Loan', 'Agricultural Loan'].map(cat => (
                  <button key={cat} onClick={() => setSearchQuery(cat)}
                    className="px-4 py-1.5 rounded-full bg-[#1a3050] border border-blue-700/40 text-blue-200 text-sm hover:border-amber-400 hover:text-amber-300 transition-all">
                    {cat}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Results */}
          {searchResults.length > 0 && (
            <div className="max-w-2xl mx-auto w-full px-6 mt-6 overflow-y-auto pb-12">
              <div className="space-y-3">
                {searchResults.map(p => (
                  <button key={p.product_id}
                    onClick={() => {
                      setShowSearch(false);
                      setTimeout(() => {
                        const el = document.querySelector(`[data-pid="${p.product_id}"]`);
                        if (el) {
                          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                          (el as HTMLElement).style.outline = '3px solid #f59e0b';
                          setTimeout(() => { (el as HTMLElement).style.outline = ''; }, 2000);
                        } else {
                          document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' });
                        }
                      }, 150);
                    }}
                    className="w-full text-left bg-[#1a3050] hover:bg-[#1e3a60] border border-blue-800/40 hover:border-amber-400/50 rounded-xl px-5 py-4 transition-all group">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="flex items-center gap-2 mb-1">
                          <span className="text-[10px] font-bold text-amber-400 bg-amber-400/10 px-2 py-0.5 rounded-full uppercase tracking-wide">{p.subcategory}</span>
                          <span className="text-[10px] text-blue-500">{p.category}</span>
                        </div>
                        <p className="text-white font-semibold text-sm group-hover:text-amber-300 transition-colors">{p.product_name}</p>
                        <p className="text-blue-400 text-xs mt-1 line-clamp-1">{p.description}</p>
                      </div>
                      <div className="text-right flex-shrink-0">
                        {rateLabel(p) && <p className={`text-sm font-bold ${rateColor(p)}`}>{rateLabel(p)}</p>}
                        <ChevronRight className="w-4 h-4 text-blue-600 group-hover:text-amber-400 mt-1 ml-auto transition-colors" />
                      </div>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {searchQuery.trim().length > 1 && searchResults.length === 0 && (
            <div className="max-w-2xl mx-auto w-full px-6 mt-12 text-center">
              <p className="text-blue-500 text-4xl mb-3">🔍</p>
              <p className="text-white font-semibold">No products match "{searchQuery}"</p>
              <p className="text-blue-400 text-sm mt-1">Try "savings", "credit card", or "mortgage"</p>
            </div>
          )}
        </div>
      )}



      {/* ══ Product Detail Modal ══════════════════════════════════════════════ */}
      {selectedProduct && (() => {
        const p = selectedProduct;
        const rate = rateLabel(p);
        const isSaved = savedProducts.has(p.product_id);
        const isInCompare = compareList.includes(p.product_id);
        const creditOk = p.min_credit_score === 0 || eligCreditScore >= p.min_credit_score;
        const incomeOk  = p.min_income === 0 || eligIncome >= p.min_income;
        const qualifies = creditOk && incomeOk;
        return (
          <div className="fixed inset-0 z-[70] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setSelectedProduct(null)} />
            <div className="relative w-full max-w-2xl bg-white rounded-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">

              {/* Header */}
              <div className="bg-gradient-to-r from-[#0F2744] to-[#1a3a6b] px-6 py-5 flex-shrink-0">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-4xl leading-none">{SUBCAT_ICONS[p.subcategory] ?? '🏦'}</span>
                    <div>
                      <h2 className="text-white font-bold text-lg leading-tight">{p.product_name}</h2>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SUBCAT_COLORS[p.subcategory] ?? 'bg-slate-100 text-slate-500'}`}>{p.subcategory}</span>
                        <span className="text-blue-300 text-xs flex items-center gap-0.5">
                          <Star className="w-3 h-3 fill-amber-400 text-amber-400" /> {p.avg_rating}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      onClick={e => toggleSave(p.product_id, e)}
                      title={isSaved ? 'Remove bookmark' : 'Save product'}
                      className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded-xl flex items-center justify-center transition-colors"
                    >
                      <Bookmark className={`w-4 h-4 ${isSaved ? 'text-amber-400 fill-amber-400' : 'text-white/70'}`} />
                    </button>
                    <button
                      onClick={() => setSelectedProduct(null)}
                      className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded-xl flex items-center justify-center transition-colors"
                    >
                      <X className="w-4 h-4 text-white" />
                    </button>
                  </div>
                </div>
                {rate && (
                  <div className={`mt-3 text-3xl font-extrabold ${
                    p.cash_back_pct > 0 ? 'text-violet-300'
                    : APR_SUBCATS.has(p.subcategory) ? 'text-orange-300'
                    : 'text-emerald-300'
                  }`}>{rate}</div>
                )}
              </div>

              {/* Scrollable body */}
              <div className="overflow-y-auto flex-1 p-6 space-y-5">
                <p className="text-slate-600 leading-relaxed">{p.description}</p>

                {/* Fees & Eligibility grid */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 rounded-2xl p-4">
                    <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Fees &amp; Balance</h3>
                    <div className="space-y-2.5">
                      {p.annual_fee === 0 && p.monthly_fee === 0 ? (
                        <div className="flex items-center gap-2 text-emerald-600 font-semibold text-sm">
                          <Check className="w-4 h-4" /> No fees
                        </div>
                      ) : (
                        <>
                          {p.annual_fee > 0 && (
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-500">Annual fee</span>
                              <span className="font-semibold text-slate-700">${p.annual_fee}/yr</span>
                            </div>
                          )}
                          {p.monthly_fee > 0 && (
                            <div className="flex justify-between text-sm">
                              <span className="text-slate-500">Monthly fee</span>
                              <span className="font-semibold text-slate-700">${p.monthly_fee}/mo</span>
                            </div>
                          )}
                          {p.fee_waiver_condition && p.fee_waiver_condition !== 'none' && (
                            <div className="text-xs text-emerald-600 bg-emerald-50 rounded-xl px-3 py-2 leading-relaxed">
                              Waiver: {p.fee_waiver_condition}
                            </div>
                          )}
                        </>
                      )}
                      {p.min_balance > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Min balance</span>
                          <span className="font-semibold text-slate-700">${p.min_balance.toLocaleString()}</span>
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="bg-slate-50 rounded-2xl p-4">
                    <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-3">Eligibility &amp; Rewards</h3>
                    <div className="space-y-2.5">
                      {p.min_credit_score > 0 ? (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Min credit score</span>
                          <span className="font-semibold text-slate-700">{p.min_credit_score}+</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 text-emerald-600 font-semibold text-sm">
                          <Check className="w-4 h-4" /> All credit scores
                        </div>
                      )}
                      {p.min_income > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Min annual income</span>
                          <span className="font-semibold text-slate-700">${p.min_income.toLocaleString()}</span>
                        </div>
                      )}
                      {p.rewards_type && p.rewards_type !== 'none' && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Rewards</span>
                          <span className="font-semibold text-slate-700 capitalize">{p.rewards_type}</span>
                        </div>
                      )}
                      {p.cash_back_pct > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Cash back</span>
                          <span className="font-semibold text-violet-600">{p.cash_back_pct}%</span>
                        </div>
                      )}
                      {p.regular_apr_pct > 0 && (
                        <div className="flex justify-between text-sm">
                          <span className="text-slate-500">Regular APR</span>
                          <span className="font-semibold text-orange-600">{p.regular_apr_pct}%</span>
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Do I Qualify? */}
                <div className="border border-slate-200 rounded-2xl p-4">
                  <h3 className="font-bold text-slate-700 mb-4 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-blue-500" />
                    Do I Qualify?
                  </h3>
                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div>
                      <label className="text-xs text-slate-500 font-medium block mb-2">
                        My credit score: <span className="font-bold text-slate-700">{eligCreditScore}</span>
                      </label>
                      <input
                        type="range" min={300} max={850}
                        value={eligCreditScore}
                        onChange={e => setEligCreditScore(Number(e.target.value))}
                        className="w-full accent-blue-600"
                      />
                      <div className="flex justify-between text-[10px] text-slate-400 mt-0.5">
                        <span>300</span><span>850</span>
                      </div>
                    </div>
                    <div>
                      <label className="text-xs text-slate-500 font-medium block mb-2">Annual income</label>
                      <div className="relative">
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 text-sm">$</span>
                        <input
                          type="number" min={0} step={5000}
                          value={eligIncome}
                          onChange={e => setEligIncome(Math.max(0, Number(e.target.value)))}
                          className="w-full border border-slate-200 rounded-xl pl-7 pr-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  </div>
                  <div className={`rounded-xl px-4 py-3 flex items-start gap-3 ${
                    qualifies ? 'bg-emerald-50 border border-emerald-200' : 'bg-red-50 border border-red-200'
                  }`}>
                    {qualifies ? (
                      <>
                        <Check className="w-5 h-5 text-emerald-600 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-emerald-700 font-semibold text-sm">You appear to qualify!</p>
                          <p className="text-emerald-600 text-xs mt-0.5">Your inputs meet the requirements for this product.</p>
                        </div>
                      </>
                    ) : (
                      <>
                        <X className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                        <div>
                          <p className="text-red-700 font-semibold text-sm">You may not qualify yet</p>
                          <p className="text-red-600 text-xs mt-0.5">
                            {!creditOk && `Credit score of ${p.min_credit_score}+ required. `}
                            {!incomeOk && `Min annual income of $${p.min_income.toLocaleString()} required.`}
                          </p>
                        </div>
                      </>
                    )}
                  </div>
                </div>
              </div>

              {/* Footer CTAs */}
              <div className={`border-t flex-shrink-0 ${applyDone ? 'border-emerald-100 bg-emerald-50' : 'border-slate-100 bg-white'}`}>
                <div className="px-6 py-4 flex items-center gap-3">
                  <button
                    onClick={() => toggleCompareById(p.product_id)}
                    disabled={!isInCompare && compareList.length >= 3}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-xl font-semibold text-sm border transition-all ${
                      isInCompare
                        ? 'bg-blue-50 border-blue-300 text-blue-700'
                        : compareList.length >= 3
                        ? 'bg-slate-50 border-slate-200 text-slate-300 cursor-not-allowed'
                        : 'bg-white border-slate-200 text-slate-600 hover:border-blue-300 hover:text-blue-600'
                    }`}
                  >
                    <BarChart2 className="w-4 h-4" />
                    {isInCompare ? 'In comparison' : compareList.length >= 3 ? 'Max 3 reached' : 'Compare'}
                  </button>
                  <div className="flex-1" />
                  {applyDone ? (
                    <div>
                      <div className="flex items-center gap-2 text-emerald-700 font-semibold text-sm">
                        <Check className="w-4 h-4" /> Application submitted!
                      </div>
                      <p className="text-emerald-600 text-xs mt-0.5">
                        A Meridian banker will contact you{userEmail ? ` at ${userEmail}` : ''} within 1 business day.
                      </p>
                    </div>
                  ) : (
                    <button
                      onClick={() => {
                        if (!firstName) { setSelectedProduct(null); setShowSignIn(true); setModalTab('register'); return; }
                        setApplyDone(true);
                        if (visitorId && sessionId) {
                          queueEvent({ visitor_id: visitorId, session_id: sessionId, product_id: p.product_id, product_category: p.subcategory, interaction_type: 'apply_click', dwell_time: 0 });
                          void flushEvents();
                        }
                      }}
                      className="bg-[#0F2744] hover:bg-[#1a3a6b] text-white font-bold text-sm px-6 py-2.5 rounded-xl transition-colors flex items-center gap-2"
                    >
                      Apply Now <ArrowRight className="w-4 h-4" />
                    </button>
                  )}
                </div>
              </div>

            </div>
          </div>
        );
      })()}

      {/* ══ Compare Tool Modal ════════════════════════════════════════════════════ */}
      {showCompareTool && (() => {
        const products = compareList
          .map(pid => allProducts.find(p => p.product_id === pid))
          .filter(Boolean) as Product[];

        const METRICS: { label: string; getValue: (p: Product) => string; bestPid: string | null }[] = (() => {
          const bestOf = (ids: string[], key: keyof Product, mode: 'min' | 'max'): string | null => {
            const vals = ids.map(id => {
              const prod = products.find(p => p.product_id === id);
              return prod ? (prod[key] as number) : 0;
            });
            const target = mode === 'max' ? Math.max(...vals) : Math.min(...vals);
            const idx = vals.indexOf(target);
            return target !== 0 || mode === 'min' ? (products[idx]?.product_id ?? null) : null;
          };
          const pids = products.map(p => p.product_id);
          return [
            { label: 'Rate / APY / APR',  getValue: (p: Product) => rateLabel(p) || ' - ',                        bestPid: null },
            { label: 'Annual Fee',        getValue: (p: Product) => p.annual_fee === 0 ? 'None' : `$${p.annual_fee}/yr`,           bestPid: bestOf(pids, 'annual_fee', 'min') },
            { label: 'Monthly Fee',       getValue: (p: Product) => p.monthly_fee === 0 ? 'None' : `$${p.monthly_fee}/mo`,         bestPid: bestOf(pids, 'monthly_fee', 'min') },
            { label: 'Fee Waiver',        getValue: (p: Product) => (p.fee_waiver_condition && p.fee_waiver_condition !== 'none') ? p.fee_waiver_condition : ' - ', bestPid: null },
            { label: 'Min Balance',       getValue: (p: Product) => p.min_balance === 0 ? 'None' : `$${p.min_balance.toLocaleString()}`,    bestPid: bestOf(pids, 'min_balance', 'min') },
            { label: 'Min Credit Score',  getValue: (p: Product) => p.min_credit_score === 0 ? 'Any' : `${p.min_credit_score}+`,  bestPid: bestOf(pids, 'min_credit_score', 'min') },
            { label: 'Min Income',        getValue: (p: Product) => p.min_income === 0 ? 'Any' : `$${p.min_income.toLocaleString()}/yr`,     bestPid: bestOf(pids, 'min_income', 'min') },
            { label: 'Cash Back',         getValue: (p: Product) => p.cash_back_pct > 0 ? `${p.cash_back_pct}%` : ' - ',             bestPid: products.some(p => p.cash_back_pct > 0) ? bestOf(pids, 'cash_back_pct', 'max') : null },
            { label: 'Regular APR',       getValue: (p: Product) => p.regular_apr_pct > 0 ? `${p.regular_apr_pct}%` : ' - ',         bestPid: null },
            { label: 'Rewards',           getValue: (p: Product) => (p.rewards_type && p.rewards_type !== 'none') ? p.rewards_type : ' - ', bestPid: null },
            { label: 'Rating',            getValue: (p: Product) => `${p.avg_rating} ★`,                        bestPid: bestOf(pids, 'avg_rating', 'max') },
          ];
        })();

        return (
          <div className="fixed inset-0 z-[80] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={() => setShowCompareTool(false)} />
            <div className="relative w-full max-w-4xl bg-white rounded-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">

              {/* Header */}
              <div className="bg-[#0F2744] px-6 py-4 flex items-center justify-between flex-shrink-0">
                <div className="flex items-center gap-3">
                  <BarChart2 className="w-5 h-5 text-amber-400" />
                  <h2 className="text-white font-bold text-lg">Product Comparison</h2>
                  <span className="bg-white/10 text-blue-200 text-xs font-semibold px-2.5 py-0.5 rounded-full">{products.length} products</span>
                </div>
                <button onClick={() => setShowCompareTool(false)} className="w-8 h-8 bg-white/10 hover:bg-white/20 rounded-xl flex items-center justify-center transition-colors">
                  <X className="w-4 h-4 text-white" />
                </button>
              </div>

              {/* Scrollable table */}
              <div className="overflow-auto flex-1">
                <table className="w-full border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="text-left px-5 py-4 text-[10px] font-bold text-slate-400 uppercase tracking-wider w-40 border-r border-slate-200">Feature</th>
                      {products.map(p => (
                        <th key={p.product_id} className="px-5 py-4 text-center min-w-[200px]">
                          <div className="flex flex-col items-center gap-1.5">
                            <span className="text-3xl leading-none">{SUBCAT_ICONS[p.subcategory] ?? '🏦'}</span>
                            <span className="text-sm font-bold text-slate-700 leading-tight max-w-[160px]">{p.product_name}</span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SUBCAT_COLORS[p.subcategory] ?? 'bg-slate-100 text-slate-500'}`}>{p.subcategory}</span>
                          </div>
                          <button
                            onClick={() => { toggleCompareById(p.product_id); if (compareList.length <= 1) setShowCompareTool(false); }}
                            className="mt-2 text-[10px] text-slate-400 hover:text-red-500 transition-colors"
                          >
                            Remove
                          </button>
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {METRICS.map((metric, mi) => (
                      <tr key={metric.label} className={mi % 2 === 0 ? 'bg-white' : 'bg-slate-50/60'}>
                        <td className="px-5 py-3.5 text-xs font-semibold text-slate-500 border-r border-slate-200">{metric.label}</td>
                        {products.map(p => {
                          const val = metric.getValue(p);
                          const isBest = metric.bestPid === p.product_id;
                          return (
                            <td key={p.product_id} className="px-5 py-3.5 text-center">
                              <span className={`text-sm font-semibold ${isBest ? 'text-emerald-600' : 'text-slate-700'}`}>{val}</span>
                              {isBest && <span className="ml-1.5 text-[10px] bg-emerald-50 text-emerald-600 border border-emerald-200 px-1.5 py-0.5 rounded-full font-bold align-middle">Best</span>}
                            </td>
                          );
                        })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Footer: per-product CTAs */}
              <div className="border-t border-slate-200 bg-slate-50 px-5 py-4 flex-shrink-0">
                <div className="flex gap-4">
                  <div className="w-40 flex-shrink-0" />
                  {products.map(p => (
                    <div key={p.product_id} className="flex-1 flex flex-col items-center gap-2">
                      <button
                        onClick={() => { setShowCompareTool(false); openProductDetail(p); }}
                        className="w-full text-xs font-semibold text-blue-700 hover:text-blue-900 underline underline-offset-2 transition-colors"
                      >
                        View Details
                      </button>
                      <button
                        onClick={() => {
                          if (!firstName) { setShowCompareTool(false); setShowSignIn(true); setModalTab('register'); return; }
                          if (visitorId && sessionId) {
                            queueEvent({ visitor_id: visitorId, session_id: sessionId, product_id: p.product_id, product_category: p.subcategory, interaction_type: 'apply_click', dwell_time: 0 });
                            void flushEvents();
                          }
                          setShowCompareTool(false);
                          openProductDetail(p);
                          setApplyDone(true);
                        }}
                        className="w-full bg-[#0F2744] hover:bg-[#1a3a6b] text-white font-bold text-sm py-2.5 rounded-xl transition-colors"
                      >
                        Apply Now
                      </button>
                    </div>
                  ))}
                </div>
              </div>

            </div>
          </div>
        );
      })()}

      {/* ══ Floating Compare Bar ══════════════════════════════════════════════════ */}
      {compareList.length > 0 && (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 bg-[#0F2744] text-white rounded-2xl shadow-2xl px-5 py-3 flex items-center gap-3 border border-white/10 max-w-[90vw]">
          <BarChart2 className="w-5 h-5 text-amber-400 flex-shrink-0" />
          <div className="flex items-center gap-2 flex-wrap">
            {compareList.map(pid => {
              const prod = allProducts.find(p => p.product_id === pid);
              if (!prod) return null;
              return (
                <div key={pid} className="flex items-center gap-1.5 bg-white/10 rounded-lg px-3 py-1.5 text-xs font-semibold">
                  <span className="text-base leading-none">{SUBCAT_ICONS[prod.subcategory] ?? '🏦'}</span>
                  <span className="max-w-[100px] truncate">{prod.product_name}</span>
                  <button onClick={() => toggleCompareById(pid)} className="ml-1 text-white/50 hover:text-white transition-colors">
                    <X className="w-3 h-3" />
                  </button>
                </div>
              );
            })}
          </div>
          {compareList.length >= 2 ? (
            <button
              onClick={() => setShowCompareTool(true)}
              className="bg-amber-400 hover:bg-amber-300 text-[#0F2744] font-bold text-sm px-4 py-2 rounded-xl transition-colors whitespace-nowrap flex-shrink-0"
            >
              Compare ({compareList.length})
            </button>
          ) : (
            <span className="text-xs text-blue-300 whitespace-nowrap flex-shrink-0">Add {2 - compareList.length} more</span>
          )}
          <button onClick={() => setCompareList([])} title="Clear all" className="text-white/40 hover:text-white/80 transition-colors flex-shrink-0 ml-1">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* ══ Profile panels ══════════════════════════════════════════════════ */}
      {activePanel && (
        <div className="fixed inset-0 z-[60] flex justify-end">
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={() => setActivePanel(null)} />
          <div className="relative w-full max-w-md bg-white shadow-2xl flex flex-col h-full overflow-hidden">

            {/* ── Panel header ── */}
            <div className="bg-[#0F2744] px-6 py-5 flex-shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-amber-400/20 rounded-xl flex items-center justify-center">
                    {activePanel === 'profile'       && <User className="w-5 h-5 text-amber-400" />}
                    {activePanel === 'preferences'   && <Settings className="w-5 h-5 text-amber-400" />}
                    {activePanel === 'saved'         && <Bookmark className="w-5 h-5 text-amber-400" />}
                    {activePanel === 'notifications' && <Bell className="w-5 h-5 text-amber-400" />}
                  </div>
                  <div>
                    <p className="text-white font-bold text-base">
                      {activePanel === 'profile' ? 'My Profile' : activePanel === 'preferences' ? 'Preferences' : activePanel === 'saved' ? 'Saved Products' : 'Notifications'}
                    </p>
                    <p className="text-blue-300 text-[11px]">
                      {activePanel === 'profile' ? 'Edit your personal details' : activePanel === 'preferences' ? 'Your financial goals and persona' : activePanel === 'saved' ? `${savedProducts.size} bookmarked product${savedProducts.size !== 1 ? 's' : ''}` : 'Manage your alerts and updates'}
                    </p>
                  </div>
                </div>
                <button onClick={() => setActivePanel(null)} className="text-blue-300 hover:text-white p-1 transition-colors">
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* ── Panel body ── */}
            <div className="flex-1 overflow-y-auto">

              {/* ─── My Profile ─── */}
              {activePanel === 'profile' && (
                <div className="p-6 space-y-5">
                  {/* Avatar */}
                  <div className="flex items-center gap-4 pb-5 border-b border-slate-100">
                    <div className="w-16 h-16 bg-[#0F2744] rounded-full flex items-center justify-center text-amber-400 text-2xl font-black flex-shrink-0">
                      {(editName || firstName || '?')[0].toUpperCase()}
                    </div>
                    <div>
                      <p className="text-slate-900 font-bold text-lg leading-tight">{editName || firstName}</p>
                      {userEmail && <p className="text-slate-500 text-sm">{editEmail || userEmail}</p>}
                      {persona && <span className="inline-block mt-1.5 text-[10px] font-bold bg-amber-100 text-amber-700 px-2.5 py-0.5 rounded-full">{persona}</span>}
                    </div>
                  </div>

                  {/* Editable fields */}
                  {[
                    { label: 'First Name', value: editName, setter: setEditName, type: 'text', placeholder: 'Your name' },
                    { label: 'Email Address', value: editEmail, setter: setEditEmail, type: 'email', placeholder: 'your@email.com' },
                    { label: 'Phone Number', value: editPhone, setter: setEditPhone, type: 'tel', placeholder: '+1 (555) 000-0000' },
                  ].map(f => (
                    <div key={f.label}>
                      <label className="block text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">{f.label}</label>
                      <input type={f.type} value={f.value} onChange={e => f.setter(e.target.value)} placeholder={f.placeholder}
                        className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                    </div>
                  ))}

                  {/* Read-only info */}
                  <div className="bg-slate-50 rounded-xl p-4 space-y-2">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2">Account Info</p>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Persona</span>
                      <span className="text-slate-900 font-semibold">{persona ?? 'Not yet assigned'}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Member Since</span>
                      <span className="text-slate-900 font-semibold">July 2026</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-slate-500">Saved Products</span>
                      <span className="text-slate-900 font-semibold">{savedProducts.size}</span>
                    </div>
                  </div>

                  <button onClick={saveProfile}
                    className="w-full py-3.5 rounded-xl font-bold text-sm flex items-center justify-center gap-2 transition-all bg-[#0F2744] hover:bg-[#1a3a5c] text-white shadow-sm">
                    {editSaved ? <><Check className="w-4 h-4 text-emerald-400" /> Saved!</> : 'Save Changes'}
                  </button>
                </div>
              )}

              {/* ─── Preferences ─── */}
              {activePanel === 'preferences' && (
                <div className="p-6 space-y-6">
                  {/* Current persona */}
                  {persona && (
                    <div className="bg-[#0F2744] rounded-2xl p-5">
                      <p className="text-[10px] font-bold text-blue-400 uppercase tracking-widest mb-2">Your Persona</p>
                      <p className="text-amber-300 font-black text-lg">{persona}</p>
                      <p className="text-blue-300 text-xs mt-1 leading-relaxed">
                        {persona === 'Wealth Builder' && 'You are focused on growing assets, home equity, and long-term investments.'}
                        {persona === 'Retiree Anchor' && 'You prioritize stability, income, and capital preservation in retirement.'}
                        {persona === 'Everyday Essential' && 'You value straightforward banking with low fees and easy access.'}
                        {persona === 'Digital Native' && 'You prefer digital-first experiences, rewards, and credit products.'}
                        {persona === 'At-Risk Saver' && 'You are building financial stability and building toward stronger credit.'}
                      </p>
                    </div>
                  )}

                  {/* Financial goals */}
                  <div>
                    <p className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-3">Financial Goals</p>
                    <div className="space-y-2">
                      {[
                        'Building my savings',
                        'Improving my credit score',
                        'Buying a home',
                        'Planning for retirement',
                        'Starting or growing a business',
                        'Agricultural or farm financing',
                        'Reducing debt',
                        'Traveling more',
                      ].map(goal => {
                        const active = prefGoals.includes(goal);
                        return (
                          <button key={goal}
                            onClick={() => savePreferences(active ? prefGoals.filter(g => g !== goal) : [...prefGoals, goal])}
                            className={`w-full flex items-center justify-between px-4 py-3 rounded-xl border text-sm font-medium transition-all ${
                              active ? 'border-blue-600 bg-blue-50 text-blue-800' : 'border-slate-200 text-slate-700 hover:border-blue-300 hover:bg-slate-50'
                            }`}>
                            {goal}
                            {active && <Check className="w-4 h-4 text-blue-600 flex-shrink-0" />}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  <p className="text-[11px] text-slate-400 text-center">Your selections help us surface the most relevant products for you.</p>
                </div>
              )}

              {/* ─── Saved Products ─── */}
              {activePanel === 'saved' && (
                <div className="p-6">
                  {savedProducts.size === 0 ? (
                    <div className="text-center py-16">
                      <div className="w-14 h-14 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                        <Bookmark className="w-7 h-7 text-slate-300" />
                      </div>
                      <p className="text-slate-900 font-bold">No saved products yet</p>
                      <p className="text-slate-500 text-sm mt-1">Click the bookmark icon on any product to save it here.</p>
                      <button onClick={() => { setActivePanel(null); document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' }); }}
                        className="mt-5 px-5 py-2.5 bg-[#0F2744] text-white text-sm font-bold rounded-xl hover:bg-[#1a3a5c] transition-colors">
                        Browse Products
                      </button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      {allProducts.filter(p => savedProducts.has(p.product_id)).map(p => (
                        <div key={p.product_id} className="bg-white border border-slate-200 rounded-2xl p-4 hover:shadow-sm transition-shadow">
                          <div className="flex items-start justify-between gap-2">
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-lg leading-none">{SUBCAT_ICONS[p.subcategory] ?? '🏦'}</span>
                                <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SUBCAT_COLORS[p.subcategory] ?? 'bg-slate-100 text-slate-500'}`}>{p.subcategory}</span>
                              </div>
                              <p className="text-slate-900 font-bold text-sm leading-snug">{p.product_name}</p>
                              {rateLabel(p) && <p className={`text-sm font-extrabold mt-0.5 ${rateColor(p)}`}>{rateLabel(p)}</p>}
                              <p className="text-slate-500 text-xs mt-1 line-clamp-2">{p.description}</p>
                            </div>
                            <button onClick={e => toggleSave(p.product_id, e)}
                              title="Remove bookmark"
                              className="flex-shrink-0 p-1.5 rounded-lg hover:bg-red-50 transition-colors">
                              <Bookmark className="w-4 h-4 text-amber-500 fill-amber-500" />
                            </button>
                          </div>
                          <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between">
                            <div className="flex items-center gap-1">
                              <Star className="w-3.5 h-3.5 text-amber-400 fill-amber-400" />
                              <span className="text-xs font-bold text-slate-700">{p.avg_rating}</span>
                            </div>
                            <button onClick={() => { setActivePanel(null); setTimeout(() => { const el = document.querySelector(`[data-pid="${p.product_id}"]`); el?.scrollIntoView({ behavior: 'smooth', block: 'center' }); }, 200); }}
                              className="text-xs text-blue-600 font-semibold hover:underline flex items-center gap-1">
                              View <ChevronRight className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ─── Notifications ─── */}
              {activePanel === 'notifications' && (
                <div className="p-6 space-y-2">
                  <p className="text-xs text-slate-400 mb-4">Choose which updates you want to receive from Meridian Bank.</p>
                  {[
                    { key: 'mrd_n_rates', label: 'Rate Alerts', desc: 'Get notified when APY or interest rates change on your saved products', val: notifRates, setter: setNotifRates },
                    { key: 'mrd_n_products', label: 'New Products', desc: 'Be the first to hear about new checking, savings, and loan products', val: notifProducts, setter: setNotifProducts },
                    { key: 'mrd_n_offers', label: 'Personalized Offers', desc: 'AI-matched offers based on your browsing and financial profile', val: notifOffers, setter: setNotifOffers },
                    { key: 'mrd_n_news', label: 'Monthly Newsletter', desc: 'A monthly digest of banking tips, community news, and rate updates', val: notifNewsletter, setter: setNotifNewsletter },
                  ].map(n => (
                    <div key={n.key} className="flex items-center justify-between gap-4 p-4 bg-white rounded-2xl border border-slate-100 hover:border-slate-200 transition-colors">
                      <div className="flex-1 min-w-0">
                        <p className="text-slate-900 font-semibold text-sm">{n.label}</p>
                        <p className="text-slate-400 text-xs mt-0.5 leading-relaxed">{n.desc}</p>
                      </div>
                      <button
                        onClick={() => toggleNotif(n.key, !n.val, n.setter)}
                        className={`relative flex-shrink-0 w-11 h-6 rounded-full transition-colors ${n.val ? 'bg-blue-600' : 'bg-slate-200'}`}>
                        <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform ${n.val ? 'translate-x-5' : ''}`} />
                      </button>
                    </div>
                  ))}

                  <div className="pt-4">
                    <div className="bg-slate-50 rounded-2xl p-4 text-center">
                      <p className="text-slate-500 text-xs">Meridian Bank will never sell your contact information to third parties.</p>
                    </div>
                  </div>
                </div>
              )}

            </div>
          </div>
        </div>
      )}

      {/* ── Navigation ──────────────────────────────────────────────────── */}
      <nav className="sticky top-0 z-40 bg-[#0F2744] border-b-[3px] border-amber-400 shadow-lg">
        <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between gap-4">
          {/* Logo */}
          <div className="flex items-center gap-2 flex-shrink-0">
            <span className="font-bold text-lg" style={{ fontFamily: "'Inter', system-ui, sans-serif", letterSpacing: '-0.3px' }}>
              <span className="text-amber-300">Meridian</span>
              <span className="text-white"> Bank</span>
            </span>
            <span className="hidden md:block text-[10px] text-sky-300 border border-sky-800/60 px-1.5 py-0.5 rounded-full">
              FDIC
            </span>
          </div>

          {/* Centre nav links */}
          <div className="hidden sm:flex items-center gap-1">
            {[
              { label: 'Products',      href: '#products' },
              { label: 'Why Meridian',  href: '#why' },
              { label: 'News',          href: '#news' },
              { label: 'Contact',       href: '#contact' },
            ].map(l => (
              <a key={l.href} href={l.href}
                className="text-blue-200 hover:text-amber-300 text-sm font-medium px-3 py-1.5 rounded-lg hover:bg-white/5 transition-all">
                {l.label}
              </a>
            ))}
          </div>

          {/* Right actions */}
          <div className="flex items-center gap-2 flex-shrink-0">
            {/* Search */}
            <button onClick={openSearch}
              className="w-8 h-8 flex items-center justify-center text-blue-300 hover:text-white hover:bg-white/10 rounded-lg transition-all"
              title="Search products">
              <Search className="w-4 h-4" />
            </button>
            <button
              onClick={() => navigate('/banking')}
              className="text-blue-300 hover:text-white text-xs font-medium transition-colors hidden md:block border border-blue-700/50 px-3 py-1.5 rounded-lg hover:border-blue-500"
            >
              ← Dashboard
            </button>
            {firstName ? (
              /* ── Profile button + dropdown ── */
              <div className="relative" ref={profileRef}>
                <button
                  onClick={() => setShowProfile(p => !p)}
                  className="flex items-center gap-2 bg-amber-400 hover:bg-amber-300 text-[#0F2744] text-sm font-bold px-3 py-1.5 rounded-lg transition-colors shadow-sm"
                >
                  <div className="w-6 h-6 bg-[#0F2744] rounded-full flex items-center justify-center text-amber-400 text-[11px] font-black">
                    {firstName[0].toUpperCase()}
                  </div>
                  {firstName.split(' ')[0]}
                </button>

                {showProfile && (
                  <div className="absolute right-0 top-full mt-2 w-72 bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-50">
                    {/* Profile header */}
                    <div className="bg-[#0F2744] px-5 py-5">
                      <div className="flex items-center gap-3">
                        <div className="w-11 h-11 bg-amber-400 rounded-full flex items-center justify-center text-[#0F2744] text-base font-black flex-shrink-0">
                          {firstName[0].toUpperCase()}
                        </div>
                        <div className="min-w-0">
                          <p className="text-white font-bold text-sm">{firstName}</p>
                          {userEmail && <p className="text-blue-300 text-xs mt-0.5 truncate">{userEmail}</p>}
                          {persona && (
                            <span className="inline-block mt-1.5 text-[10px] font-bold bg-amber-400/20 border border-amber-400/30 text-amber-300 px-2 py-0.5 rounded-full">
                              {persona}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Menu */}
                    <div className="p-2">
                      <p className="px-3 pt-2 pb-1 text-[10px] uppercase tracking-widest font-bold text-slate-400">Account</p>
                      {[
                        { icon: <User className="w-4 h-4" />, label: 'My Profile', desc: 'View and edit your details', panel: 'profile' as const },
                        { icon: <Settings className="w-4 h-4" />, label: 'Preferences', desc: `${persona ?? 'Personalization'} settings`, panel: 'preferences' as const },
                        { icon: <Bookmark className="w-4 h-4" />, label: 'Saved Products', desc: `${savedProducts.size} product${savedProducts.size !== 1 ? 's' : ''} bookmarked`, panel: 'saved' as const },
                        { icon: <Bell className="w-4 h-4" />, label: 'Notifications', desc: 'Rate alerts and updates', panel: 'notifications' as const },
                      ].map(item => (
                        <button key={item.label} onClick={() => openPanel(item.panel)}
                          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-slate-50 transition-colors text-left">
                          <span className="text-slate-400">{item.icon}</span>
                          <div>
                            <p className="text-slate-900 font-semibold text-sm">{item.label}</p>
                            <p className="text-slate-400 text-xs">{item.desc}</p>
                          </div>
                        </button>
                      ))}

                      <div className="mx-3 my-2 border-t border-slate-100" />

                      <button
                        onClick={handleLogout}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl hover:bg-red-50 transition-colors text-left mb-1">
                        <LogOut className="w-4 h-4 text-red-500" />
                        <div>
                          <p className="text-red-600 font-semibold text-sm">Sign Out</p>
                          <p className="text-slate-400 text-xs">You will need to sign in again</p>
                        </div>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              /* ── Sign In button ── */
              <button
                onClick={() => { setModalTab('register'); setShowSignIn(true); }}
                className="bg-amber-400 text-[#0F2744] text-sm font-bold px-4 py-1.5 rounded-lg hover:bg-amber-300 transition-colors shadow-sm"
              >
                Sign In
              </button>
            )}
          </div>
        </div>
      </nav>

      {/* ── Hero ─────────────────────────────────────────────────────────── */}
      <section className={`transition-opacity duration-500 ${heroReady ? 'opacity-100' : 'opacity-0'} ${
        personalized
          ? 'bg-gradient-to-br from-[#0F2744] via-[#1E40AF] to-teal-700'
          : 'bg-gradient-to-br from-[#0F2744] via-[#1B4ED8] to-blue-600'
      } text-white`}>
        <div className="max-w-6xl mx-auto px-6 py-16 md:py-20">
          <div className="flex flex-col lg:flex-row items-center gap-12">

            {/* Left  -  headline + CTA */}
            <div className="flex-1 min-w-0">
              {firstName && personalized && (
                <div className="inline-flex items-center gap-2 bg-emerald-500/20 border border-emerald-400/40 text-emerald-300 text-xs font-bold px-3 py-1.5 rounded-full mb-6 tracking-wide">
                  <span>👋</span> Welcome back, {firstName}!
                </div>
              )}
              <p className="text-blue-300/70 text-[11px] uppercase tracking-[3px] mb-3 font-semibold">
                {firstName && personalized && persona ? `Personalized for · ${persona}` : 'Est. 2001 · Member FDIC · $12B Assets'}
              </p>
              <h1
                className="text-4xl md:text-5xl lg:text-6xl font-bold leading-[1.1] mb-5"
                style={{ fontFamily: "'Inter', system-ui, sans-serif" }}
              >
                <span className="bg-gradient-to-r from-amber-300 via-yellow-200 to-white bg-clip-text text-transparent">
                  {hero.headline}
                </span>
              </h1>
              <p className="text-blue-100 text-lg leading-relaxed mb-8 max-w-xl" style={{ fontWeight: 300 }}>
                {hero.subhead}
              </p>
              <div className="flex flex-wrap gap-3 items-center">
                <button
                  onClick={onCTA}
                  className={`flex items-center gap-2 font-bold px-7 py-3.5 rounded-xl text-sm shadow-lg transition-all hover:scale-105 active:scale-95 ${
                    personalized ? 'bg-emerald-500 hover:bg-emerald-400 text-white' : 'bg-amber-500 hover:bg-amber-400 text-amber-950'
                  }`}
                >
                  {hero.cta_label} <ArrowRight className="w-4 h-4" />
                </button>
              </div>
            </div>


          </div>
        </div>
      </section>

      {/* ── Trust bar ────────────────────────────────────────────────────── */}
      <div className="bg-[#091c36] border-b border-[#1a3a5c]">
        <div className="max-w-6xl mx-auto px-6 py-3.5 flex flex-wrap gap-6 justify-center sm:justify-between text-xs font-semibold">
          <span className="flex items-center gap-1.5 text-sky-300"><Shield className="w-3.5 h-3.5" /> FDIC Insured up to $250K</span>
          <span className="flex items-center gap-1.5 text-amber-300"><Star className="w-3.5 h-3.5 fill-amber-300" /> 4.6 / 5 customer rating</span>
          <span className="flex items-center gap-1.5 text-emerald-300"><Users className="w-3.5 h-3.5" /> 850K+ customers</span>
          <span className="flex items-center gap-1.5 text-violet-300"><TrendingUp className="w-3.5 h-3.5" /> Est. 2001 · $12B assets</span>
        </div>
      </div>

      {/* ── First-Timer Popular Picks  -  always visible unless personalized picks are shown ── */}
      {/* Condition: hide ONLY when the signed-in personalized section below will render.    */}
      {/* Previously used !personalized, but a cookie-tracked returning visitor can have     */}
      {/* personalized=true with no firstName → both sections disappeared.                  */}
      {!(firstName && personalized && personalizedCards.length > 0) && (() => {
        // Pin the 3 default hero products by ID  -  no filter needed, no API dependency.
        // Uses live API data when available; falls back to FALLBACK on first render.
        const DEFAULT_PICK_IDS = ['MRD_P001', 'MRD_P002', 'MRD_P003'];
        const picks: Product[] = DEFAULT_PICK_IDS
          .map(id => allProducts.find(p => p.product_id === id) ?? FALLBACK.find(p => p.product_id === id))
          .filter((p): p is Product => Boolean(p));

        if (picks.length === 0) return null;

        return (
          <section className="bg-white border-b border-slate-200">
            <div className="max-w-6xl mx-auto px-6 py-10">
              <div className="flex items-center justify-between mb-6 gap-4 flex-wrap">
                <div>
                  <p className="text-xs uppercase tracking-widest font-bold text-blue-600 mb-1">Most Popular</p>
                  <h2 className="text-xl font-bold text-slate-900">Where most customers start</h2>
                  <p className="text-slate-500 text-sm mt-0.5">No credit check · Open in minutes · FDIC insured</p>
                </div>
                <button
                  onClick={() => setShowSignIn(true)}
                  className="flex-shrink-0 px-5 py-2.5 rounded-xl bg-[#0F2744] hover:bg-blue-900 text-white font-bold text-sm transition-colors"
                >
                  Sign in for personalized picks →
                </button>
              </div>

              <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
                {picks.map((p, i) => (
                  <div
                    key={p.product_id}
                    onClick={() => { onCardClick(p); openProductDetail(p); }}
                    className="group relative bg-white/95 backdrop-blur-sm rounded-2xl border border-white/20 cursor-pointer transition-all duration-200 hover:shadow-2xl hover:-translate-y-1 flex flex-col"
                  >
                    {i === 0 && (
                      <div className="absolute -top-3 left-5">
                        <span className="bg-amber-400 text-amber-950 text-[10px] font-bold px-3 py-1 rounded-full flex items-center gap-1 shadow-md">
                          <Star className="w-3 h-3 fill-amber-950" /> Most Popular
                        </span>
                      </div>
                    )}
                    <div className="p-5 flex-1 flex flex-col">
                      <div className="flex items-start justify-between gap-2 mb-3">
                        <span className="text-3xl leading-none">{SUBCAT_ICONS[p.subcategory] ?? '🏦'}</span>
                        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${SUBCAT_COLORS[p.subcategory] ?? 'bg-slate-100 text-slate-500'}`}>
                          {p.subcategory}
                        </span>
                      </div>
                      <h3 className="font-bold text-[#0F2744] text-sm leading-snug mb-1.5">{p.product_name}</h3>
                      {rateLabel(p) && (
                        <p className={`font-extrabold text-xl mb-2 leading-none ${rateColor(p)}`}>{rateLabel(p)}</p>
                      )}
                      <p className="text-slate-500 text-xs leading-relaxed mb-4 flex-1 line-clamp-3">{p.description}</p>
                      <div className="space-y-1.5 text-xs">
                        <div className="flex items-center gap-1.5 text-emerald-600 font-semibold">
                          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0" />
                          No fees · No credit check
                        </div>
                        {p.avg_rating && (
                          <div className="flex items-center gap-1 text-amber-600 font-medium">
                            <Star className="w-3 h-3 fill-amber-400 text-amber-400" />
                            {p.avg_rating} rating
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="px-5 pb-4">
                      <button
                        type="button"
                        onClick={e => { e.stopPropagation(); openProductDetail(p); }}
                        className="w-full py-2 rounded-xl bg-[#0F2744] text-white text-xs font-bold hover:bg-blue-900 transition-colors"
                      >
                        Learn More
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>
        );
      })()}

      {/* ── Personalized Picks (signed-in users only) ─────────────────────── */}
      {firstName && personalized && personalizedCards.length > 0 && (
        <section className="bg-gradient-to-r from-emerald-50 via-blue-50 to-indigo-50 border-b border-blue-100">
          <div className="max-w-6xl mx-auto px-6 py-12">
            <div className="flex items-start justify-between mb-7">
              <div>
                <p className="text-xs uppercase tracking-widest font-bold text-emerald-600 mb-1.5">Personalized for You</p>
                <h2 style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
                  <span className="text-2xl font-bold text-[#0F2744]">Your </span>
                  <span className="text-2xl font-bold text-emerald-600 italic">top</span>
                  <span className="text-2xl font-bold text-[#0F2744]"> picks</span>
                </h2>
              </div>
              <div className="relative flex items-center gap-2 mt-1">
                <span className="bg-[#0F2744] text-white text-xs font-bold px-3 py-1.5 rounded-lg">{persona}</span>
                <button onClick={() => setShowWhyTip(v => !v)} className="text-slate-400 hover:text-slate-600 transition-colors">
                  <Info className="w-4 h-4" />
                </button>
                {showWhyTip && (
                  <div className="absolute right-0 top-9 w-72 bg-white border border-slate-200 shadow-2xl rounded-xl p-4 z-20">
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-semibold text-slate-800 text-sm">Why these products?</span>
                      <button onClick={() => setShowWhyTip(false)}><X className="w-4 h-4 text-slate-400" /></button>
                    </div>
                    <p className="text-slate-600 text-xs leading-relaxed">
                      Based on the products you explored in your last visit, we identified you as a{' '}
                      <strong>{persona}</strong> customer. These picks match your financial interests.
                      No personal data is collected without your consent.
                    </p>
                  </div>
                )}
              </div>
            </div>
            <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
              {personalizedCards.map((p, i) => renderCard(p, i))}
            </div>
          </div>
        </section>
      )}

      {/* ── Full Product Catalog ──────────────────────────────────────────── */}
      <section id="products" className="max-w-6xl mx-auto px-6 py-14">
        <p className="text-xs uppercase tracking-widest font-bold text-teal-600 mb-2">Complete Catalog</p>
        <h2 className="mb-8" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
          <span className="text-2xl font-bold text-[#0F2744]">{allProducts.length} products  - </span>{' '}
          <span className="text-2xl font-bold text-blue-600">personal,</span>{' '}
          <span className="text-2xl font-bold text-emerald-600">business</span>{' '}
          <span className="text-2xl font-bold text-[#0F2744]">&amp;</span>{' '}
          <span className="text-2xl font-bold text-amber-600">agricultural</span>{' '}
          <span className="text-2xl font-bold text-[#0F2744]">banking</span>
        </h2>

        {/* Category tabs */}
        <div className="flex items-center gap-0 mb-5 border-b border-slate-200 overflow-x-auto">
          {([
            { key: 'all'          as const, label: 'All Products', count: allProducts.length, emoji: '' },
            { key: 'Personal'     as const, label: 'Personal',     count: countCat('Personal'), emoji: '👤' },
            { key: 'Business'     as const, label: 'Business',     count: countCat('Business'), emoji: '🏢' },
            { key: 'Agricultural' as const, label: 'Agricultural', count: countCat('Agricultural'), emoji: '🌾' },
          ]).map(tab => (
            <button
              key={tab.key}
              onClick={() => { setActiveTab(tab.key); setActiveSubcat('All'); }}
              className={`flex items-center gap-2 px-5 py-3 text-sm font-semibold whitespace-nowrap border-b-2 -mb-px transition-all ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-700'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {tab.emoji && <span>{tab.emoji}</span>}
              {tab.label}
              <span className={`text-[11px] px-1.5 py-0.5 rounded-full font-bold min-w-[22px] text-center ${
                activeTab === tab.key ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-500'
              }`}>
                {tab.count}
              </span>
            </button>
          ))}
        </div>

        {/* Subcategory chips */}
        {chips && (
          <div className="flex flex-wrap gap-2 mb-7">
            {chips.map(chip => {
              const count = chip === 'All'
                ? allProducts.filter(p => p.category === activeTab).length
                : allProducts.filter(p => p.category === activeTab && (CHIP_SUBCATS[chip] ?? []).includes(p.subcategory)).length;
              return (
                <button
                  key={chip}
                  onClick={() => setActiveSubcat(chip)}
                  className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all ${
                    activeSubcat === chip
                      ? 'bg-[#0F2744] text-white shadow-sm'
                      : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                  }`}
                >
                  {chip} <span className={`ml-0.5 ${activeSubcat === chip ? 'opacity-60' : 'opacity-50'}`}>({count})</span>
                </button>
              );
            })}
          </div>
        )}

        {/* Product grid */}
        {filteredProducts.length > 0 ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {filteredProducts.map(p => {
              const recIdx = personalizedCards.findIndex(r => r.product_id === p.product_id);
              return renderCard(p, recIdx >= 0 ? recIdx : undefined);
            })}
          </div>
        ) : (
          <div className="py-16 text-center text-slate-400">
            <p className="text-base font-semibold mb-2">No products match this filter</p>
            <button onClick={() => setActiveSubcat('All')} className="text-sm text-blue-600 hover:underline">Clear filter</button>
          </div>
        )}
      </section>

      {/* ── Why Meridian ─────────────────────────────────────────────────── */}
      <section id="why">
        {/* Stats bar */}
        <div className="bg-[#0F2744] border-t border-blue-900/50">
          <div className="max-w-6xl mx-auto px-6 py-10">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
              {[
                { value: '$13.4B', label: 'Total Assets' },
                { value: '850K+', label: 'Customers Served' },
                { value: '4.6★', label: 'Average Rating' },
                { value: 'Est. 2001', label: '25 Years of Trust' },
              ].map(s => (
                <div key={s.label}>
                  <p className="text-3xl font-black text-amber-300 tabular-nums">{s.value}</p>
                  <p className="text-blue-300 text-xs mt-1 uppercase tracking-widest">{s.label}</p>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Headline + 6-item benefit grid */}
        <div className="bg-white border-t border-slate-100">
          <div className="max-w-6xl mx-auto px-6 py-16">
            <p className="text-xs uppercase tracking-widest font-bold text-amber-600 mb-2">Why Meridian</p>
            <h2 className="text-3xl font-bold text-[#0F2744] mb-12" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              Banking built around <span className="text-blue-600 italic">your</span> life
            </h2>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[
                {
                  icon: <Shield className="w-6 h-6 text-sky-600" />,
                  bg: 'bg-sky-50',
                  title: 'Bank-grade security',
                  titleColor: 'text-sky-800',
                  body: 'FDIC-insured deposits, 256-bit encryption, and 24/7 fraud monitoring protect every dollar you hold with us.',
                },
                {
                  icon: <TrendingUp className="w-6 h-6 text-emerald-600" />,
                  bg: 'bg-emerald-50',
                  title: 'Rates that reward you',
                  titleColor: 'text-emerald-800',
                  body: 'Industry-leading APY on savings, CDs, and money market accounts  -  no teaser rates, no hidden catches.',
                },
                {
                  icon: <Users className="w-6 h-6 text-violet-600" />,
                  bg: 'bg-violet-50',
                  title: 'Relationship banking',
                  titleColor: 'text-violet-800',
                  body: 'Dedicated bankers available by phone, branch, or in-app. Our average customer relationship spans 11 years.',
                },
                {
                  icon: <Bot className="w-6 h-6 text-blue-600" />,
                  bg: 'bg-blue-50',
                  title: 'AI-powered personalization',
                  titleColor: 'text-blue-800',
                  body: 'Our AI matches you with the exact right product for your life stage and goals  -  not a generic brochure.',
                },
                {
                  icon: <Star className="w-6 h-6 text-teal-600" />,
                  bg: 'bg-teal-50',
                  title: 'No surprise fees',
                  titleColor: 'text-teal-800',
                  body: 'Transparent pricing. Every fee, rate, and waiver condition listed up front before you ever apply.',
                },
                {
                  icon: <Globe2 className="w-6 h-6 text-amber-600" />,
                  bg: 'bg-amber-50',
                  title: 'Community roots',
                  titleColor: 'text-amber-800',
                  body: '12% of net income reinvested locally  -  small business grants, rural housing, and community programs.',
                },
              ].map(item => (
                <div key={item.title} className="flex gap-4 p-5 rounded-2xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow bg-white">
                  <div className={`flex-shrink-0 w-12 h-12 ${item.bg} rounded-xl flex items-center justify-center`}>
                    {item.icon}
                  </div>
                  <div>
                    <h3 className={`font-bold mb-1.5 text-sm ${item.titleColor}`}>{item.title}</h3>
                    <p className="text-slate-500 text-sm leading-relaxed">{item.body}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Awards strip */}
        <div className="bg-slate-50 border-t border-slate-200">
          <div className="max-w-6xl mx-auto px-6 py-8">
            <div className="flex flex-wrap items-center justify-center gap-8">
              {[
                { badge: 'Bankrate', desc: 'Best Community Bank 2024–2026' },
                { badge: '4.6 / 5', desc: 'App Store · 180K reviews' },
                { badge: 'FDIC', desc: 'Insured · $250K coverage' },
                { badge: '#1', desc: 'Agricultural Lender · Illinois 2025' },
              ].map(a => (
                <div key={a.badge} className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#0F2744] flex items-center justify-center flex-shrink-0">
                    <Award className="w-5 h-5 text-amber-400" />
                  </div>
                  <div>
                    <p className="text-[#0F2744] font-black text-sm">{a.badge}</p>
                    <p className="text-slate-500 text-xs">{a.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* CTA strip */}
        <div className="bg-[#0F2744]">
          <div className="max-w-6xl mx-auto px-6 py-10 flex flex-col sm:flex-row items-center justify-between gap-6">
            <div>
              <p className="text-white text-xl font-bold">Ready to get started?</p>
              <p className="text-blue-300 text-sm mt-1">Open an account in under 5 minutes  -  no branch visit needed.</p>
            </div>
            <div className="flex items-center gap-4 flex-shrink-0">
              <button
                onClick={() => setShowSignIn(true)}
                className="bg-amber-400 hover:bg-amber-300 text-[#0F2744] font-bold px-7 py-3 rounded-xl text-sm transition-colors shadow-lg">
                Open an Account
              </button>
              <a href="#products" className="text-blue-300 hover:text-white text-sm font-medium transition-colors">
                Explore Products →
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ── Newsroom ─────────────────────────────────────────────────────── */}
      <section id="news" className="bg-slate-50 border-t border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <p className="text-xs uppercase tracking-widest font-bold text-amber-600 mb-2">Newsroom</p>
          <div className="flex items-end justify-between mb-10 gap-4">
            <h2 className="text-3xl font-bold text-[#0F2744]" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              Latest from Meridian
            </h2>
            <div className="flex gap-2 shrink-0">
              {['All', 'Earnings', 'Product', 'Community', 'Rate Update', 'Awards', 'Technology'].map(cat => (
                <span key={cat} className="hidden lg:block text-[10px] font-bold uppercase tracking-widest text-slate-400">{cat === 'All' ? '' : '·'}</span>
              ))}
            </div>
          </div>

          {/* Featured article */}
          {NEWS_ARTICLES.filter(a => a.featured).map(a => (
            <div key={a.id} className="mb-8 rounded-2xl overflow-hidden shadow-md border border-blue-900/10">
              <div className="bg-gradient-to-r from-[#0F2744] via-[#1B3D6F] to-blue-800 p-8 md:p-10">
                <span className="text-[11px] font-black bg-amber-400 text-[#0F2744] px-3 py-1 rounded-full uppercase tracking-wide">
                  {a.category}
                </span>
                <h3 className="text-white font-bold text-2xl leading-snug mt-4 mb-3 max-w-2xl">{a.title}</h3>
                <p className="text-blue-200 text-sm leading-relaxed max-w-2xl">{a.excerpt}</p>
                <div className="flex items-center gap-5 mt-5 text-blue-400 text-xs">
                  <span className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5" />{a.date}</span>
                  <span className="flex items-center gap-1.5"><Clock className="w-3.5 h-3.5" />{a.readMin} min read</span>
                  <span className="text-amber-400 font-semibold cursor-pointer hover:text-amber-300 transition-colors">Read full story →</span>
                </div>
              </div>
            </div>
          ))}

          {/* Article grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {NEWS_ARTICLES.filter(a => !a.featured).map(a => (
              <div key={a.id} className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-md transition-shadow cursor-pointer group">
                <div className="flex items-center gap-2 mb-3">
                  <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wide ${
                    a.category === 'Rate Update' ? 'bg-emerald-100 text-emerald-700' :
                    a.category === 'Awards'      ? 'bg-amber-100 text-amber-700' :
                    a.category === 'Technology'  ? 'bg-purple-100 text-purple-700' :
                    a.category === 'Community'   ? 'bg-teal-100 text-teal-700' :
                    'bg-blue-100 text-blue-700'
                  }`}>{a.category}</span>
                  <span className="text-[10px] text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />{a.date}
                  </span>
                </div>
                <h3 className="text-slate-900 font-bold text-sm leading-snug mb-2 group-hover:text-blue-700 transition-colors">{a.title}</h3>
                <p className="text-slate-500 text-xs leading-relaxed line-clamp-3">{a.excerpt}</p>
                <p className="text-blue-600 text-xs mt-3 font-semibold group-hover:text-blue-700 transition-colors">{a.readMin} min read →</p>
              </div>
            ))}
          </div>

          {/* Newsletter strip */}
          <div className="mt-12 bg-[#0F2744] rounded-2xl p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
            <div>
              <p className="text-white font-bold text-base">Stay in the loop</p>
              <p className="text-blue-300 text-sm mt-1">Get rate updates, product news, and community highlights in your inbox.</p>
            </div>
            <div className="flex gap-2 w-full sm:w-auto">
              <input type="email" placeholder="your@email.com"
                className="flex-1 sm:w-56 border border-blue-700 bg-white/10 text-white placeholder-blue-400 rounded-xl px-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-amber-400" />
              <button className="bg-amber-400 hover:bg-amber-300 text-[#0F2744] font-bold px-5 py-2.5 rounded-xl text-sm transition-colors flex-shrink-0">
                Subscribe
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* ── Contact ──────────────────────────────────────────────────────── */}
      <section id="contact" className="bg-white border-t border-slate-200">
        <div className="max-w-6xl mx-auto px-6 py-16">
          <p className="text-xs uppercase tracking-widest font-bold text-amber-600 mb-2">Contact</p>
          <h2 className="text-3xl font-bold text-[#0F2744] mb-10" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
            Get in touch
          </h2>

          {/* Quick contact cards */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-12">
            {[
              { icon: <Phone className="w-6 h-6 text-blue-600" />, bg: 'bg-blue-50', label: 'Call Us', value: '1-800-MERIDIAN', sub: 'Mon–Fri 7am–10pm CT' },
              { icon: <Mail className="w-6 h-6 text-emerald-600" />, bg: 'bg-emerald-50', label: 'Email', value: 'support@meridianbank.com', sub: 'Reply within 1 business day' },
              { icon: <MessageCircle className="w-6 h-6 text-amber-600" />, bg: 'bg-amber-50', label: 'Live Chat', value: 'Start a conversation', sub: 'Avg. wait under 2 minutes' },
            ].map(c => (
              <div key={c.label} className={`${c.bg} rounded-2xl p-6 flex items-start gap-4`}>
                <div className="w-11 h-11 bg-white rounded-xl flex items-center justify-center shadow-sm flex-shrink-0">
                  {c.icon}
                </div>
                <div>
                  <p className="text-slate-900 font-bold text-sm">{c.label}</p>
                  <p className="text-slate-700 text-sm mt-0.5">{c.value}</p>
                  <p className="text-slate-400 text-xs mt-0.5">{c.sub}</p>
                </div>
              </div>
            ))}
          </div>

          {/* Branch locations */}
          <h3 className="text-[#0F2744] font-bold text-lg mb-5 flex items-center gap-2">
            <MapPin className="w-5 h-5 text-amber-500" /> Branch Locations
          </h3>
          <div className="grid md:grid-cols-3 gap-4 mb-14">
            {BRANCHES.map(b => (
              <div key={b.name} className="border border-slate-200 rounded-2xl p-5 hover:shadow-md transition-shadow">
                <p className="text-[#0F2744] font-bold text-sm mb-2">{b.name}</p>
                <p className="text-slate-500 text-sm">{b.address}</p>
                <p className="text-slate-500 text-sm">{b.city}</p>
                <div className="mt-3 pt-3 border-t border-slate-100 flex flex-col gap-1">
                  <span className="text-blue-600 text-sm font-medium">{b.phone}</span>
                  <span className="text-slate-400 text-xs flex items-center gap-1.5"><Clock className="w-3 h-3" />{b.hours}</span>
                </div>
              </div>
            ))}
          </div>

          {/* Form + Why reach out */}
          <div className="grid md:grid-cols-2 gap-12">
            {/* Form */}
            <div>
              <h3 className="text-[#0F2744] font-bold text-lg mb-6">Send us a message</h3>
              {ctxSent ? (
                <div className="text-center py-12 border border-emerald-200 rounded-2xl bg-emerald-50">
                  <div className="w-14 h-14 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-3">
                    <svg className="w-7 h-7 text-emerald-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}><path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" /></svg>
                  </div>
                  <p className="text-slate-900 font-bold">Message sent!</p>
                  <p className="text-slate-500 text-sm mt-1">We'll get back to you within one business day.</p>
                  <button onClick={() => { setCtxSent(false); setCtxName(''); setCtxEmail(''); setCtxMsg(''); }}
                    className="mt-4 text-blue-600 text-sm hover:underline">Send another message</button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">Full Name</label>
                    <input type="text" value={ctxName} onChange={e => setCtxName(e.target.value)} placeholder="Your name"
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">Email Address</label>
                    <input type="email" value={ctxEmail} onChange={e => setCtxEmail(e.target.value)} placeholder="your@email.com"
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-slate-500 uppercase tracking-widest mb-1.5">Message</label>
                    <textarea value={ctxMsg} onChange={e => setCtxMsg(e.target.value)} placeholder="How can we help you today?" rows={5}
                      className="w-full border border-slate-200 rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 transition resize-none" />
                  </div>
                  <button onClick={handleContactSend} disabled={ctxSending || !ctxName.trim() || !ctxEmail.trim() || !ctxMsg.trim()}
                    className="w-full bg-[#0F2744] hover:bg-[#1a3a5c] disabled:opacity-50 text-white font-bold py-3.5 rounded-xl text-sm transition-colors flex items-center justify-center gap-2">
                    {ctxSending
                      ? <><span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" /> Sending…</>
                      : <><Send className="w-4 h-4" /> Send Message</>}
                  </button>
                </div>
              )}
            </div>

            {/* Why reach out */}
            <div>
              <h3 className="text-[#0F2744] font-bold text-lg mb-6">How we can help</h3>
              <div className="space-y-5">
                {[
                  { title: 'Account questions', desc: 'Balance inquiries, statement requests, account closure  -  handled promptly, no hold music.' },
                  { title: 'Product guidance', desc: 'Not sure which savings or loan product fits your goals? A relationship banker will walk you through it.' },
                  { title: 'Loan applications', desc: 'Start your mortgage, auto, or business loan conversation before you ever visit a branch.' },
                  { title: 'Fraud & disputes', desc: 'Noticed something suspicious? Our fraud team responds within 30 minutes, around the clock.' },
                  { title: 'Technical support', desc: 'Online banking issues, app bugs, or password resets  -  our tech team is one call or chat away.' },
                ].map(r => (
                  <div key={r.title} className="flex gap-3">
                    <div className="w-1.5 h-1.5 rounded-full bg-amber-400 flex-shrink-0 mt-2" />
                    <div>
                      <p className="text-slate-900 font-semibold text-sm">{r.title}</p>
                      <p className="text-slate-500 text-xs mt-0.5 leading-relaxed">{r.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-8 p-5 bg-[#0F2744] rounded-2xl">
                <p className="text-amber-300 font-bold text-sm">Priority support for Premier members</p>
                <p className="text-blue-300 text-xs mt-1 leading-relaxed">Premier and Private Banking clients receive a dedicated relationship manager with a direct line  -  no queue, no transfers.</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── CTA Band ─────────────────────────────────────────────────────── */}
      <section className="bg-[#0F2744] text-white">
        <div className="max-w-6xl mx-auto px-6 py-12 flex flex-col sm:flex-row items-center justify-between gap-6">
          <div>
            <h2 className="text-xl font-bold mb-1" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>
              <span className="text-amber-300">Ready</span>
              <span className="text-white"> to get started?</span>
            </h2>
            <p className="text-blue-200/70 text-sm" style={{ fontWeight: 300 }}>
              Open an account in under 5 minutes  -  no branch visit needed.
            </p>
          </div>
          <button
            onClick={() => { if (personalized) { onCTA(); } else { setShowSignIn(true); } }}
            className="flex-shrink-0 flex items-center gap-2 bg-amber-500 hover:bg-amber-400 text-amber-950 font-bold px-7 py-3.5 rounded-xl text-sm shadow-lg transition-all hover:scale-105 active:scale-95"
          >
            {personalized ? hero.cta_label : 'Open Your Account'} <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </section>

      {/* ── Footer ───────────────────────────────────────────────────────── */}
      <footer className="bg-slate-950 text-slate-500">
        <div className="max-w-6xl mx-auto px-6 py-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <span className="text-lg">🏦</span>
            <span className="text-slate-300 font-bold" style={{ fontFamily: "'Inter', system-ui, sans-serif" }}>Meridian Bank</span>
            <span className="text-xs">· Member FDIC</span>
          </div>
          <div className="text-xs text-center">© 2025 Meridian Bank · 123 Financial District · Privacy Policy · Terms</div>
          {visitNumber >= 2 && (
            <div className="text-xs text-slate-700 italic">Personalized experience · Visit #{visitNumber}</div>
          )}
        </div>
      </footer>

      {/* ── Chatbot Widget ────────────────────────────────────────────────── */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col items-end gap-3">

        {/* Chat window */}
        {chatOpen && (
          <div className="w-80 bg-white rounded-2xl shadow-2xl border border-slate-200 flex flex-col overflow-hidden" style={{ maxHeight: '520px' }}>

            {/* Header */}
            <div className="bg-[#0F2744] px-4 py-3 flex items-center justify-between flex-shrink-0">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 bg-amber-400 rounded-full flex items-center justify-center flex-shrink-0">
                  <Bot className="w-4 h-4 text-[#0F2744]" />
                </div>
                <div>
                  <p className="text-white font-bold text-sm leading-none">Meridian Guide</p>
                  <p className="text-blue-300 text-[10px] mt-0.5">Product finder · 5 quick questions</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {chatDone && (
                  <button onClick={resetChat} className="text-blue-300 hover:text-white text-[10px] font-medium transition-colors">
                    Restart
                  </button>
                )}
                <button onClick={() => setChatOpen(false)} className="text-blue-300 hover:text-white transition-colors">
                  <X className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Progress bar */}
            {!chatDone && (
              <div className="h-1 bg-slate-100 flex-shrink-0">
                <div
                  className="h-full bg-emerald-500 transition-all duration-500"
                  style={{ width: `${(chatStep / CHAT_QUESTIONS.length) * 100}%` }}
                />
              </div>
            )}

            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-4 py-3 space-y-3 min-h-0">
              {chatMessages.map(msg => (
                <div key={msg.id}>
                  {msg.type === 'bot' && (
                    <div className="flex items-start gap-2">
                      <div className="w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                        <Bot className="w-3.5 h-3.5 text-blue-700" />
                      </div>
                      <div className="bg-slate-100 rounded-2xl rounded-tl-sm px-3 py-2 max-w-[85%]">
                        <p className="text-slate-800 text-xs leading-relaxed" style={{ whiteSpace: 'pre-line' }}>{msg.text}</p>
                      </div>
                    </div>
                  )}
                  {msg.type === 'user' && (
                    <div className="flex justify-end">
                      <div className="bg-[#0F2744] text-white rounded-2xl rounded-tr-sm px-3 py-2 max-w-[80%]">
                        <p className="text-xs font-medium">{msg.text}</p>
                      </div>
                    </div>
                  )}
                  {msg.type === 'products' && msg.products && msg.products.length > 0 && (
                    <div className="space-y-2 mt-1">
                      {msg.products.map((p, i) => (
                        <div key={p.product_id} className={`rounded-xl border p-3 ${i === 0 ? 'border-emerald-300 bg-emerald-50' : 'border-slate-200 bg-white'}`}>
                          <div className="flex items-start justify-between gap-1 mb-1">
                            <span className="text-sm">{SUBCAT_ICONS[p.subcategory] ?? '🏦'}</span>
                            {i === 0 && <span className="text-[9px] font-bold text-emerald-700 bg-emerald-100 px-1.5 py-0.5 rounded-full">Best Match</span>}
                          </div>
                          <button
                            className="text-xs font-bold text-[#0F2744] hover:text-blue-600 hover:underline leading-snug mb-0.5 text-left w-full flex items-center gap-1 group/link"
                            onClick={() => {
                              setChatOpen(false);
                              setTimeout(() => {
                                const el = document.querySelector(`[data-pid="${p.product_id}"]`);
                                if (el) {
                                  el.scrollIntoView({ behavior: 'smooth', block: 'center' });
                                  (el as HTMLElement).style.outline = '3px solid #059669';
                                  setTimeout(() => { (el as HTMLElement).style.outline = ''; }, 2000);
                                } else {
                                  document.getElementById('products')?.scrollIntoView({ behavior: 'smooth' });
                                }
                              }, 100);
                            }}
                          >
                            {p.product_name}
                            <ChevronRight className="w-3 h-3 opacity-0 group-hover/link:opacity-100 transition-opacity flex-shrink-0" />
                          </button>
                          {rateLabel(p) && <p className={`text-xs font-bold ${rateColor(p)}`}>{rateLabel(p)}</p>}
                          <p className="text-[10px] text-slate-500 mt-1 leading-relaxed line-clamp-2">{p.description}</p>
                        </div>
                      ))}
                      <p className="text-[10px] text-slate-400 text-center pt-1">
                        Tap a product name to jump to it in the catalog ↑
                      </p>
                    </div>
                  )}
                </div>
              ))}
              <div ref={chatEndRef} />
            </div>

            {/* Answer options for current question */}
            {/* Predefined option chips  -  guided flow */}
            {!chatDone && chatStep < CHAT_QUESTIONS.length && (
              <div className="px-3 pt-2 pb-1 border-t border-slate-100 flex-shrink-0">
                <p className="text-[9px] text-slate-400 font-medium mb-1.5 uppercase tracking-wide">Quick pick</p>
                <div className="flex flex-wrap gap-1.5">
                  {CHAT_QUESTIONS[chatStep].options.map(opt => (
                    <button
                      key={opt.value}
                      onClick={() => handleChatAnswer(CHAT_QUESTIONS[chatStep].id, opt)}
                      className="px-3 py-1.5 rounded-full border border-blue-200 bg-blue-50 hover:bg-blue-600 hover:text-white hover:border-blue-600 text-blue-700 text-xs font-semibold transition-all"
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {chatDone && (
              <div className="px-3 pt-2 pb-1 border-t border-slate-100 flex-shrink-0">
                <a
                  href="#products"
                  onClick={() => setChatOpen(false)}
                  className="block w-full text-center bg-[#0F2744] hover:bg-[#1a3a5c] text-white text-xs font-bold py-2 rounded-xl transition-colors mb-2"
                >
                  See full catalog ↓
                </a>
              </div>
            )}

            {/* Free-text input  -  always visible */}
            <div className="px-3 pb-3 flex-shrink-0">
              <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5">
                <input
                  ref={chatInputRef}
                  type="text"
                  value={chatInput}
                  onChange={e => setChatInput(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleSendMessage(); }}
                  placeholder="Ask anything…"
                  className="flex-1 bg-transparent text-xs text-slate-800 placeholder-slate-400 outline-none min-w-0"
                  disabled={chatLoading}
                />
                <button
                  onClick={handleSendMessage}
                  disabled={!chatInput.trim() || chatLoading}
                  className="flex-shrink-0 w-6 h-6 rounded-full bg-[#0F2744] disabled:bg-slate-300 flex items-center justify-center transition-colors"
                >
                  {chatLoading
                    ? <span className="w-2.5 h-2.5 border border-white border-t-transparent rounded-full animate-spin" />
                    : <ChevronRight className="w-3.5 h-3.5 text-white" />
                  }
                </button>
              </div>
              <p className="text-[9px] text-slate-400 mt-1 text-center">Powered by Meridian AI · Not financial advice</p>
            </div>
          </div>
        )}

        {/* Floating button */}
        <button
          onClick={() => setChatOpen(v => !v)}
          className={`w-14 h-14 rounded-full shadow-xl flex items-center justify-center transition-all hover:scale-110 active:scale-95 ${
            chatOpen ? 'bg-slate-700 hover:bg-slate-600' : 'bg-[#0F2744] hover:bg-[#1a3a5c]'
          }`}
        >
          {chatOpen
            ? <X className="w-5 h-5 text-white" />
            : (
              <div className="relative">
                <MessageCircle className="w-6 h-6 text-white" />
                {!chatDone && (
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-amber-400 rounded-full border-2 border-white" />
                )}
              </div>
            )
          }
        </button>
      </div>

    </div>
  );
}
