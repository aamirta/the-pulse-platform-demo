import { Outlet, useLocation } from 'react-router-dom';
import TopNav from './TopNav';
import LeftSidebar from './LeftSidebar';
import RightSidebar from './RightSidebar';
import Footer from './Footer';
import { ErrorBoundary } from '@/components/ErrorBoundary';
import { useState, useEffect, useRef, useCallback } from 'react';

export default function AppLayout() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const isHome = location.pathname === '/';

  const drawerRef = useRef<HTMLElement | null>(null);
  // Remembers what opened the drawer so focus can be handed back on close.
  const triggerRef = useRef<HTMLElement | null>(null);

  const closeMenu = useCallback(() => setMobileMenuOpen(false), []);

  const toggleMenu = useCallback(() => {
    setMobileMenuOpen((open) => {
      if (!open) triggerRef.current = document.activeElement as HTMLElement;
      return !open;
    });
  }, []);

  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  // While the drawer is open it behaves like a modal: Escape closes it, Tab is
  // trapped inside it, and the page behind does not scroll. Without this a
  // keyboard user could tab out of the drawer onto content hidden behind the
  // overlay.
  useEffect(() => {
    if (!mobileMenuOpen) return;

    const drawer = drawerRef.current;
    const focusable = () =>
      Array.from(
        drawer?.querySelectorAll<HTMLElement>(
          'a[href], button:not([disabled]), input, select, textarea, [tabindex]:not([tabindex="-1"])',
        ) ?? [],
      ).filter((el) => el.offsetParent !== null);

    focusable()[0]?.focus();

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault();
        closeMenu();
        return;
      }
      if (event.key !== 'Tab') return;

      const items = focusable();
      if (items.length === 0) return;
      const first = items[0];
      const last = items[items.length - 1];

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.addEventListener('keydown', onKeyDown);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';

    return () => {
      document.removeEventListener('keydown', onKeyDown);
      document.body.style.overflow = previousOverflow;
    };
  }, [mobileMenuOpen, closeMenu]);

  // Hand focus back to whatever opened the drawer.
  useEffect(() => {
    if (!mobileMenuOpen && triggerRef.current) {
      triggerRef.current.focus();
      triggerRef.current = null;
    }
  }, [mobileMenuOpen]);

  return (
    <div className="min-h-screen bg-background text-foreground transition-all duration-200 ease-in-out">
      <TopNav onMenuToggle={toggleMenu} mobileMenuOpen={mobileMenuOpen} />

      {/* Lets keyboard users jump past the whole navigation to the content. */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[60] focus:rounded-md focus:bg-card focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-foreground focus:shadow-soft-lg focus:outline-none focus:ring-2 focus:ring-pulse-orange"
      >
        Aller au contenu principal
      </a>

      <div className="flex pt-16">
        {/* Left Sidebar - Desktop */}
        <aside className="hidden lg:block fixed left-0 top-16 w-[260px] h-[calc(100vh-64px)] bg-card/70 backdrop-blur-md border-r border-border/40 overflow-y-auto z-30 transition-all duration-200 ease-in-out shadow-soft-sm">
          <LeftSidebar />
        </aside>

        {/* Mobile Sidebar Overlay */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 bg-zinc-950/40 backdrop-blur-xs z-40 lg:hidden transition-opacity duration-200"
            onClick={closeMenu}
            aria-hidden="true"
          />
        )}

        {/* Mobile Sidebar.
            `inert` keeps its links out of the tab order and away from screen
            readers while it is translated off-canvas — previously 16 invisible
            links stayed focusable at every width below lg. */}
        <aside
          ref={drawerRef}
          id="mobile-navigation"
          role="dialog"
          aria-modal="true"
          aria-label="Navigation"
          inert={!mobileMenuOpen}
          aria-hidden={mobileMenuOpen ? undefined : true}
          className={`fixed left-0 top-16 w-[260px] h-[calc(100vh-64px)] bg-card border-r border-border/40 overflow-y-auto z-50 lg:hidden transition-all duration-300 ease-in-out shadow-soft-lg ${
            mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
          }`}
        >
          <LeftSidebar />
        </aside>

        {/* Main Content */}
        <main
          id="main-content"
          className={`flex-1 min-w-0 overflow-x-hidden ${isHome ? 'lg:mr-[340px]' : ''}`}
        >
          <div className="lg:ml-[260px] p-4 sm:p-5 lg:p-6 flex flex-col min-h-[calc(100vh-64px)]">
            {/* Scoped to the page area: a failing page keeps the nav, footer
                and language switcher usable instead of blanking the app.
                resetKey clears the error when the user navigates elsewhere. */}
            <div className="flex-1 animate-fade-in">
              <ErrorBoundary resetKey={location.pathname + location.search}>
                <Outlet />
              </ErrorBoundary>
            </div>
            <Footer />
          </div>
        </main>

        {/* Right Sidebar - Homepage only */}
        {isHome && (
          <aside className="hidden lg:block fixed right-0 top-16 w-[340px] h-[calc(100vh-64px)] bg-background border-l border-border/30 overflow-y-auto z-30 p-4 transition-all duration-200 ease-in-out">
            <RightSidebar />
          </aside>
        )}
      </div>
    </div>
  );
}
