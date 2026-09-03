import { lazy, Suspense, type ReactNode } from 'react';
import { HashRouter, Routes, Route, Navigate } from 'react-router-dom';
import AppLayout from '@/components/layout/AppLayout';
import { ProtectedRoute } from '@/components/ProtectedRoute';
import Home from '@/pages/Home';

// Only the landing page is bundled eagerly. Everything else is split per route:
// the whole app previously shipped as one 1.38 MB chunk, so a visitor paid for
// the charting, visualiser and dashboard code before seeing the home page.
const Startups = lazy(() => import('@/pages/Startups'));
const StartupProfile = lazy(() => import('@/pages/StartupProfile'));
const Founders = lazy(() => import('@/pages/Founders'));
const FounderProfile = lazy(() => import('@/pages/FounderProfile'));
const Investors = lazy(() => import('@/pages/Investors'));
const Incubators = lazy(() => import('@/pages/Incubators'));
const InvestorProfile = lazy(() => import('@/pages/InvestorProfile'));
const News = lazy(() => import('@/pages/News'));
const Events = lazy(() => import('@/pages/Events'));
const Opportunities = lazy(() => import('@/pages/Opportunities'));
const Analytics = lazy(() => import('@/pages/Analytics'));
const Guides = lazy(() => import('@/pages/Guides'));
const Search = lazy(() => import('@/pages/Search'));
const AIAssistant = lazy(() => import('@/pages/AIAssistant'));
const UserDashboard = lazy(() => import('@/pages/UserDashboard'));
const EcosystemVisualizer = lazy(() => import('@/pages/EcosystemVisualizer'));
const Login = lazy(() => import('@/pages/Login'));
const Onboarding = lazy(() => import('@/pages/Onboarding'));
const ForgotPassword = lazy(() => import('@/pages/ForgotPassword'));
const ResetPassword = lazy(() => import('@/pages/ResetPassword'));
const Inbox = lazy(() => import('@/pages/Inbox'));
const DealRoom = lazy(() => import('@/pages/DealRoom'));
const BadgeDownload = lazy(() => import('@/pages/BadgeDownload'));
const CommunityNewsfeed = lazy(() => import('@/pages/CommunityNewsfeed'));
const Talents = lazy(() => import('@/pages/Talents'));
const DealRoomAccess = lazy(() => import('@/pages/DealRoomAccess'));
const NotFound = lazy(() => import('@/pages/NotFound'));

/** Shown while a route chunk loads; mirrors the in-app loading treatment. */
function RouteFallback() {
  return (
    <div className="min-h-[60vh] flex items-center justify-center" role="status" aria-live="polite">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-pulse-orange border-t-transparent" />
      <span className="sr-only">Chargement…</span>
    </div>
  );
}

/** Wraps a lazily-loaded route element in its loading boundary. */
function Lazy({ children }: { children: ReactNode }) {
  return <Suspense fallback={<RouteFallback />}>{children}</Suspense>;
}

function App() {
  return (
    <HashRouter>
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Home />} />
          <Route path="/startups" element={<Lazy><Startups /></Lazy>} />
          <Route path="/startups/:id" element={<Lazy><StartupProfile /></Lazy>} />
          <Route path="/founders" element={<Lazy><Founders /></Lazy>} />
          <Route path="/founders/:id" element={<Lazy><FounderProfile /></Lazy>} />
          <Route path="/investors" element={<Lazy><Investors /></Lazy>} />
          <Route path="/incubators" element={<Lazy><Incubators /></Lazy>} />
          <Route path="/investors/:id" element={<Lazy><InvestorProfile /></Lazy>} />
          <Route path="/news" element={<Lazy><News /></Lazy>} />
          <Route path="/events" element={<Lazy><Events /></Lazy>} />
          <Route path="/opportunities" element={<Lazy><Opportunities /></Lazy>} />
          <Route path="/analytics" element={<Lazy><Analytics /></Lazy>} />
          <Route path="/guides" element={<Lazy><Guides /></Lazy>} />
          <Route path="/search" element={<Lazy><Search /></Lazy>} />
          <Route path="/ai-assistant" element={<Lazy><AIAssistant /></Lazy>} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Lazy><UserDashboard /></Lazy>
              </ProtectedRoute>
            }
          />
          <Route path="/visualizer" element={<Lazy><EcosystemVisualizer /></Lazy>} />
          <Route path="/login" element={<Lazy><Login /></Lazy>} />
          <Route path="/onboarding" element={<Lazy><Onboarding /></Lazy>} />
          {/* "Créer un compte" links point here. The route was missing, so
              #/register was a 404 while the sign-up form sat on /onboarding. */}
          <Route path="/register" element={<Lazy><Onboarding /></Lazy>} />
          <Route path="/talents" element={<Lazy><Talents /></Lazy>} />
          {/* Clean URLs for the views the sidebar reaches through a query
              parameter, so they survive being typed, shared or refreshed. */}
          <Route path="/venture-studios" element={<Navigate to="/startups?type=venture-studio" replace />} />
          <Route path="/experts" element={<Navigate to="/founders?type=expert" replace />} />
          <Route path="/cofounders" element={<Navigate to="/founders?type=co-founder" replace />} />
          <Route path="/blog" element={<Navigate to="/news?type=blog" replace />} />
          <Route path="/forgot-password" element={<Lazy><ForgotPassword /></Lazy>} />
          <Route path="/reset-password" element={<Lazy><ResetPassword /></Lazy>} />
          <Route
            path="/inbox"
            element={
              <ProtectedRoute>
                <Lazy><Inbox /></Lazy>
              </ProtectedRoute>
            }
          />
          <Route
            path="/deal-room"
            element={
              <ProtectedRoute fallback={<Lazy><DealRoomAccess /></Lazy>}>
                <Lazy><DealRoom /></Lazy>
              </ProtectedRoute>
            }
          />
          <Route
            path="/badge"
            element={
              <ProtectedRoute>
                <Lazy><BadgeDownload /></Lazy>
              </ProtectedRoute>
            }
          />
          <Route path="/newsfeed" element={<Lazy><CommunityNewsfeed /></Lazy>} />
          <Route path="*" element={<Lazy><NotFound /></Lazy>} />
        </Route>
      </Routes>
    </HashRouter>
  );
}

export default App;
