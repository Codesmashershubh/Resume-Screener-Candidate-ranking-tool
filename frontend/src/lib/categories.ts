// Mirrors the category names in backend/app/parsing/skills_taxonomy.py
// (SKILLS_BY_CATEGORY keys) - kept as a plain list here since the frontend
// doesn't need the full ~150-skill breakdown, just the category names for
// the "disciplines we understand" showcase.
export const SKILL_CATEGORIES = [
  "Engineering",
  "Data & Analytics",
  "Product & Design",
  "Marketing & Growth",
  "Sales & Business",
  "Finance & Operations",
  "People & Leadership",
] as const;
