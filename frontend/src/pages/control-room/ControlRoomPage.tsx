import { useQuery } from "@tanstack/react-query";
import { fetchControlRoom } from "@/features/control-room/api";
import { controlRoomFixture } from "@/mocks/fixtures/controlRoom.fixture";
import { EmptyState } from "@/shared/ui";
import { ControlRoomGrid } from "./ControlRoomGrid";

export function ControlRoomPage() {
  const { data, error, failureReason } = useQuery({
    queryKey: ["control-room"],
    queryFn: ({ signal }) => fetchControlRoom(signal),
    placeholderData: controlRoomFixture,
  });
  const liveFailed = Boolean(error ?? failureReason);

  if (error && !data) {
    return (
      <EmptyState
        testId="control-room-error"
        title="Control Room is unavailable"
        message={
          "The API is unreachable and no fixture is cached. " +
          "Check the FastAPI container and reload."
        }
      />
    );
  }

  return (
    <ControlRoomGrid
      data={data ?? controlRoomFixture}
      liveFailed={liveFailed}
    />
  );
}
