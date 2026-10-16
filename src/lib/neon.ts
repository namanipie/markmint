import { neon } from "@neondatabase/serverless";

/**
 * Neon Lakebase Postgres serverless client.
 * Uses HTTP pipeline transport for low-latency queries in serverless/edge environments.
 * Uses pooled connection string from process.env.DATABASE_URL.
 */
const connectionString = process.env.DATABASE_URL || "";

export const sql = neon(connectionString);

/**
 * Health check helper to verify database connectivity.
 */
export async function checkNeonConnection() {
  try {
    const result = await sql`SELECT 1 as connected, current_database() as database, version() as version`;
    return {
      ok: true,
      data: result[0],
    };
  } catch (error: any) {
    return {
      ok: false,
      error: error.message,
    };
  }
}
