# Polynesian Map — Proposal

## Why

Replace the placeholder 2×2 grid with a real map: Polynesia (Pacific island groups). Same game rules; board becomes an Earth-style graph with thematic setup and metadata for future use (UI, balance, expansions).

## What Changes

- **Map**: 2×2 grid → fixed Polynesian territory set (8 territories, explicit adjacency graph).
- **Territory IDs**: A/B/C/D → canonical IDs (e.g. `hawaii`, `samoa`, …). Each territory has metadata: `region`, `display_name`.
- **Initial ownership**: Thematic, fixed. Red = Western Polynesia (Hawaii, Samoa, Tonga, Fiji). Blue = Eastern Polynesia (Tahiti, Marquesas, Cook Islands, Easter Island). Same every game.
- **Start state**: Deterministic; no random setup.

## Capabilities

### Modified
- `territory-game`: Board is Polynesian graph; territories carry region/display_name metadata; initial ownership and start state are fixed.

### New
- (none)

## Non-goals

- No new combat rules.
- No sea zones or amphibious rules; adjacency is the only movement/attack graph.
- No random or scenario-based initial setup.

## Impact

Refactor `territory` (or map) module to graph + metadata; update UI to use territory list and (later) map art. Tests and callers that assume 4 territories or grid positions must be updated.
