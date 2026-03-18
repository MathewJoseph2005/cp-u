import { createClient } from "@supabase/supabase-js";

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseKey = import.meta.env.VITE_SUPABASE_KEY;

if (!supabaseUrl || !supabaseKey) {
  throw new Error("Missing VITE_SUPABASE_URL or VITE_SUPABASE_KEY");
}

export const supabase = createClient(supabaseUrl, supabaseKey);

export async function fetchAnalysisResults() {
  const { data, error } = await supabase.from("AnalysisResult").select("*");

  if (error) {
    throw new Error(error.message || "Failed to fetch AnalysisResult");
  }

  return Array.isArray(data) ? data : [];
}
