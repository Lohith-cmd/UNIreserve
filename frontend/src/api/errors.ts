import axios from "axios";

export function getErrorMessage(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
    return err.message;
  }
  if (err instanceof Error) return err.message;
  return "Something went wrong";
}