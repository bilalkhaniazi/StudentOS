"use client";

import { useEffect } from "react";
import { isLoopbackAlias, publicOriginFromRequest } from "@/lib/auth-config";

/** Auth.js sometimes navigates to localhost after sign-out. Bounce in the browser too. */
export function OriginGuard() {
  useEffect(() => {
    if (!isLoopbackAlias(window.location.hostname)) return;
    window.location.replace(
      publicOriginFromRequest(window.location.pathname, window.location.search).toString()
    );
  }, []);
  return null;
}
