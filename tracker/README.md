# Tracker (deterministic app) — Sujatha's existing code lands here

Plain day-block tracker (no model). It consumes the agent's blocks JSON.

Integration seam: expose one entry point, e.g. `render(blocks_json)`, matching the output
contract in `agent/skills/compose-baby-day/SKILL.md`. Confirm the field names
(`kind`, `is_focus`, `show_in_minimum_day`) match the tracker so the agent's JSON drops in
without a translation layer.
