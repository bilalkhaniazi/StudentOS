import { handlers } from "@/auth";
import { NextRequest } from "next/server";
import { PUBLIC_APP_ORIGIN } from "@/lib/auth-config";

function withPublicOrigin(req: NextRequest) {
  const publicUrl = new URL(PUBLIC_APP_ORIGIN);
  const url = new URL(req.url);
  url.protocol = publicUrl.protocol;
  url.hostname = publicUrl.hostname;
  url.port = publicUrl.port;

  const host = publicUrl.port ? `${publicUrl.hostname}:${publicUrl.port}` : publicUrl.hostname;
  req.headers.set("host", host);
  req.headers.set("x-forwarded-host", host);
  req.headers.set("x-forwarded-proto", publicUrl.protocol.replace(":", ""));
  req.headers.set("x-forwarded-port", publicUrl.port || "80");

  return new NextRequest(url, req);
}

export function GET(req: NextRequest) {
  return handlers.GET(withPublicOrigin(req));
}

export function POST(req: NextRequest) {
  return handlers.POST(withPublicOrigin(req));
}
