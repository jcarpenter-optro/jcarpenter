# Code Evaluation Guidelines

Apply these principles whenever evaluating, comparing, or reporting on code across a codebase.

## 1. Use authoritative sources, not filesystem structure

Directory listings are unreliable as an inventory of a library's public surface.
Always read the index file (index.ts, __init__.py, mod.rs, etc.) to determine what is actually exported and considered public.
A file at `components/layout/modal.gts` exporting `ModalLayout` is a top-level component — the directory nesting is an implementation detail, not a categorization signal.

## 2. Never hardcode stats derived from manual analysis

If you write a script or tool to generate data, derive all summary numbers from that same data — never hand-count and hardcode.
When a script says 82 and a dashboard says 68, that discrepancy is a bug, not two valid perspectives.
Always reconcile intermediate results before presenting them.

## 3. Name matching is necessary but not sufficient for semantic comparison

Two components that do the same thing may have different names across libraries.
A component named `Help` in one library may be `Tooltip` in another.
Before declaring something missing or unique, check whether the concept exists under a different name by reading the code or exports of both sides.
Conversely, the same name in two libraries does not guarantee equivalent functionality — verify the actual API surface.

## 4. Validate counts against multiple methods before reporting

If counting via directory scan gives X and counting via exports gives Y, investigate why before presenting either number.
Discrepancies between methods often reveal hidden components, utilities masquerading as components, or components in non-obvious locations.

## 5. Distinguish public API from implementation internals

Sub-components, test utilities, internal helpers, and re-exports of external libraries should not be counted the same as user-facing components.
Use the public exports as the canonical list and flag internal-only items separately.

## 6. Seek functional equivalents before declaring gaps

When something appears to exist on only one side:
- Search for it by concept, not just by name
- Check if it exists as a different abstraction (e.g., a modifier vs a component)
- Read the code of the nearest-named equivalent to check for overlap
