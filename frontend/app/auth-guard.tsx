'use client';

import { fetchAuthSession } from 'aws-amplify/auth';
import { usePathname, useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

const protectedRoutes = ['/chat', '/reports', '/thinking-logs', '/what-if', '/alerts', '/approvals', '/dashboard'];

function isProtectedRoute(pathname: string) {
  return pathname === '/' || protectedRoutes.some((route) => pathname === route || pathname.startsWith(`${route}/`));
}

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(isProtectedRoute(pathname));

  useEffect(() => {
    if (!isProtectedRoute(pathname)) {
      setIsChecking(false);
      return;
    }

    setIsChecking(true);

    if (process.env.NEXT_PUBLIC_DEMO_MODE === 'true') {
      setIsChecking(false);
      return;
    }

    let isMounted = true;

    fetchAuthSession()
      .then((session) => {
        if (!session.tokens?.accessToken && isMounted) {
          router.replace('/login');
        }
      })
      .catch(() => {
        if (isMounted) {
          router.replace('/login');
        }
      })
      .finally(() => {
        if (isMounted) {
          setIsChecking(false);
        }
      });

    return () => {
      isMounted = false;
    };
  }, [pathname, router]);

  if (isChecking) {
    return <main className="flex min-h-screen items-center justify-center">Loading...</main>;
  }

  return children;
}