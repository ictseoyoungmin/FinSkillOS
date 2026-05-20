import { ApiError, getJson } from "@/shared/api/client";
import { apiEndpoints } from "@/shared/api/endpoints";
import { controlRoomFixture } from "@/mocks/fixtures/controlRoom.fixture";
import type { ControlRoomData } from "./types";

/**
 * Read the Control Room snapshot.
 *
 * Slice 13.6 strategy:
 *  - In the browser, prefer the live `/api/control-room` payload but
 *    fall back to the deterministic fixture if the API is offline.
 *    That keeps the cockpit usable during early dev when the FastAPI
 *    container isn't running.
 *  - The fixture path is also reachable directly via
 *    `apiEndpoints.controlRoomMock` for Playwright visual baselines.
 *
 * Slice 13.6 cleanup §7:
 *   Fixture fallback is for the Slice 13.6 development shell only.
 *   Once non-fixture API routes land (live regime / news / events /
 *   trade memory), live DB error handling must surface the failure
 *   to the user rather than silently degrade to a fixture — pages
 *   like Risk Firewall would otherwise hide real guard violations.
 *   Track this in .devmd/13_7 / 13_8 / 13_9 before promoting any
 *   route to live data.
 */
export async function fetchControlRoom(
  signal?: AbortSignal,
): Promise<ControlRoomData> {
  try {
    return await getJson<ControlRoomData>(apiEndpoints.controlRoom, { signal });
  } catch (error) {
    if (error instanceof ApiError && error.status >= 500) {
      throw error;
    }
    // Network error, 404, CORS, or aborted — degrade to fixture so
    // the cockpit always renders the visual baseline.
    return controlRoomFixture;
  }
}
