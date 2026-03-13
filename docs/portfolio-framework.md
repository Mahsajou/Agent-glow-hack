# Portfolio Framework (12 Aspects)

The Persona agent extracts and renders data for 12 portfolio aspects to produce high-quality, comprehensive portfolios.

## The 12 Aspects

| # | Aspect | Research fields | HTML section |
|---|--------|-----------------|--------------|
| 1 | Identity | full_name, bio, mission_statement, focus_areas, values | Hero, About |
| 2 | Skills | skills, tools_technologies, methodologies, domain_expertise | Skills & Expertise |
| 3 | Projects | projects (name, outcome, impact_metrics, process_notes, url) | Key Projects |
| 4 | Process | process_notes per project | Key Projects |
| 5 | Impact | achievements, impact_statements | Impact & Results |
| 6 | Range | industries, project_types | Range & Depth |
| 7 | Depth | specialization | Range & Depth |
| 8 | Credibility | awards, publications, talks_presentations, certifications | Credibility |
| 9 | Journey | career_highlights, learning_milestones | Journey |
| 10 | Personality | interests_hobbies, personal_philosophy | About, Writing |
| 11 | Communication | writing_samples | Writing & Thinking |
| 12 | Future | future_vision, research_interests | Future Vision |

## Data Flow

- **Search** — Aspect-aware queries (identity, credibility, projects, personality)
- **Research** — Exa Research with expanded schema for all 12 aspects
- **Vibe** — layout_density (project-heavy / story-heavy / balanced), tone
- **HTML** — Sections aligned with the framework; projects use structured format with fallback to notable_projects

## Schema (research.json)

See `agent/lib/exa_client.py` `RESEARCH_OUTPUT_SCHEMA` for the full structure. Key additions:

- `projects`: array of `{name, description, outcome, impact_metrics, process_notes, url, role}`
- `mission_statement`, `focus_areas`, `values`
- `tools_technologies`, `methodologies`, `domain_expertise`
- `impact_statements`, `specialization`, `awards`, `publications`, `talks_presentations`
- `career_highlights`, `learning_milestones`, `personal_philosophy`, `future_vision`, `research_interests`
