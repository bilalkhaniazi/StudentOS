import { Auth } from "@auth/core";
import type { AuthConfig } from "@auth/core";
import { NextRequest } from "next/server";
import { buildAuthConfig } from "@/auth";
import { PUBLIC_APP_ORIGIN } from "@/lib/auth-config";

function toPublicRequest(req: NextRequest): Request {
  const publicUrl = new URL(PUBLIC_APP_ORIGIN);
  const url = new URL(req.url);
  url.protocol = publicUrl.protocol;
  url.hostname = publicUrl.hostname;
  url.port = publicUrl.port;

  const headers = new Headers();
  req.headers.forEach((value, key) => {
    const name = key.toLowerCase();
    if (name === "host" || name.startsWith("x-forwarded-")) return;
    headers.append(key, value);
  });
  headers.set("host", `${publicUrl.hostname}:${publicUrl.port}`);

  const init = { method: req.method, headers } as RequestInit & { duplex?: "half" };
  if (req.method !== "GET" && req.method !== "HEAD" && req.body) {
    init.body = req.body;
    init.duplex = "half";
  }
  return new Request(url, init);
}

async function handle(req: NextRequest) {
  return Auth(toPublicRequest(req), buildAuthConfig() as AuthConfig);
}

export const GET = handle;
export const POST = handle;
