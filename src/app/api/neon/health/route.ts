import { NextResponse } from "next/server";
import { checkNeonConnection } from "@/lib/neon";

export const dynamic = "force-dynamic";

export async function GET() {
  const result = await checkNeonConnection();
  if (!result.ok) {
    return NextResponse.json(
      {
        status: "error",
        service: "Neon Postgres",
        detail: result.error,
      },
      { status: 500 }
    );
  }

  return NextResponse.json({
    status: "ok",
    service: "Neon Postgres",
    branch: process.env.NEON_BRANCH || "production",
    data: result.data,
  });
}
