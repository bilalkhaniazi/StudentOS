import { handlers } from "@/auth";
import { NextRequest } from "next/server";
import { PUBLIC_APP_ORIGIN } from "@/lib/auth-config";

function withPublicOrigin(req: NextRequest) {
  const url = new URL(req.url);
  const publicUrl = new URL(PUBLIC_APP_ORIGIN);
  url.protocol = publicUrl.protocol;
  url.hostname = publicUrl.hostname;
  url.port = publicUrl.port;
  return new NextRequest(url, req);
}

export function GET(req: NextRequest) {
  return handlers.GET(withPublicOrigin(req));
}

export function POST(req: NextRequest) {
  return handlers.POST(withPublicOrigin(req));
}
