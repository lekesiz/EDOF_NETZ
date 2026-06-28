"use client";

const stateMap: Record<string, string> = {
  accepted: "success",
  inTraining: "info",
  terminated: "info",
  serviceDoneValidated: "success",
  serviceDoneDeclared: "warning",
  validated: "info",
  waitingAcceptation: "warning",
  notProcessed: "default",
  billed: "success",
  paid: "success",
  draft: "default",
  finalized: "success",
  canceledByAttendee: "danger",
  canceledByOrganism: "danger",
  canceledByFinancer: "danger",
  refusedByAttendee: "danger",
  refusedByOrganism: "danger",
  refusedByFinancer: "danger",
  rejected: "danger",
};

export function StatusBadge({ state }: { state: string | null }) {
  const variant = state ? stateMap[state] || "default" : "default";
  return <span className={`badge badge-${variant}`}>{state || "—"}</span>;
}
