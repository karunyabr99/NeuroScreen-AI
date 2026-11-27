import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDateTime(isoString: string): string {
  if (!isoString) return "N/A";
  const date = new Date(isoString);
  return date.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  });
}

export function formatRiskTier(tier: string): { label: string; color: string; bg: string; border: string } {
  switch (tier) {
    case "LOW_LIKELIHOOD":
      return {
        label: "Low Risk Likelihood",
        color: "text-emerald-700",
        bg: "bg-emerald-50",
        border: "border-emerald-200"
      };
    case "MODERATE_MONITOR":
      return {
        label: "Moderate (Monitor Recommended)",
        color: "text-amber-700",
        bg: "bg-amber-50",
        border: "border-amber-200"
      };
    case "ELEVATED_TRIAGE_RECOMMENDED":
      return {
        label: "Elevated Triage Recommended",
        color: "text-rose-700",
        bg: "bg-rose-50",
        border: "border-rose-200"
      };
    case "INCONCLUSIVE_MODEL_UNCALIBRATED":
    default:
      return {
        label: "Uncalibrated Research Mode",
        color: "text-sky-700",
        bg: "bg-sky-50",
        border: "border-sky-200"
      };
  }
}

export function downloadBlobAsFile(blob: Blob, filename: string): void {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.style.display = "none";
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  setTimeout(() => {
    if (a.parentNode) {
      a.parentNode.removeChild(a);
    }
    window.URL.revokeObjectURL(url);
  }, 1500);
}
