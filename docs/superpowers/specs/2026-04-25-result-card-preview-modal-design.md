# Result Card Preview Modal Design

## Summary

This design adds a click-to-enlarge preview experience for search result cards in the web frontend.
When a user clicks a result card, the app opens a full-screen modal overlay that shows the annotated frame at a much larger size so users can inspect detection details without squinting at the grid view.

The design keeps the change frontend-only.
It reuses the existing annotated frame URL and does not require any backend or API changes.

## Current State

The results grid currently renders each match as a compact card in `web/src/components/ResultCard.tsx`.
Each card shows:

1. The annotated preview image
2. The source video name
3. The matched timestamp
4. Detection and clothing tags

This works for scanning many results quickly, but the preview image is too small for close inspection.
Users cannot currently enlarge a result without manually opening the image in the browser.

## Goals

1. Let users click a result card to view a much larger preview.
2. Keep the interaction lightweight and intuitive.
3. Preserve the current search flow and result grid layout.
4. Make the modal work well on both desktop and mobile screens.
5. Support keyboard dismissal with `Esc`.

## Non-Goals

1. No backend changes
2. No image zoom/pan gestures in this phase
3. No previous/next carousel navigation in this phase
4. No full metadata redesign for result cards
5. No change to search result ranking or grouping

## Design Principles

1. Make the most common action obvious: click the card to inspect it.
2. Reuse current data instead of introducing a second fetch path.
3. Keep state local to the results panel because the preview only matters inside the search results experience.
4. Ensure dismissal is easy and predictable.

## Interaction Design

### Open

When the user clicks a result card, the application opens a centered modal overlay above the current page.

The modal displays:

1. A large annotated image
2. The video name
3. The timestamp
4. A short hint that the user can click outside or press `Esc` to close

### Close

The modal can be closed in three ways:

1. Click the close button
2. Click the backdrop outside the modal content
3. Press `Esc`

### Mobile Behavior

On smaller screens, the modal remains full-screen with padded edges.
The image scales to fit the viewport width and height without overflowing.
Metadata remains visible below or above the image depending on available space, but the image remains the visual priority.

## Component Design

### `SearchResultsPanel`

`web/src/components/SearchResultsPanel.tsx` becomes the owner of preview state.

It should maintain:

- `previewResult: SearchResult | null`

Responsibilities:

1. Pass an `onPreview` callback into each `ResultCard`
2. Open the modal when a result is clicked
3. Close the modal when dismissal is requested
4. Pass the selected result and video name into the preview modal

This keeps the modal state near the grid that created it.

### `ResultCard`

`web/src/components/ResultCard.tsx` should become an interactive card.

Responsibilities:

1. Accept an `onPreview` callback prop
2. Trigger preview on click
3. Remain semantically accessible as an interactive element
4. Show a subtle visual cue that the card is clickable

To keep the card keyboard-accessible, the card should render as a button-like interactive surface rather than a passive article with a click handler.

### `ResultPreviewModal`

Add a new lightweight component:

- `web/src/components/ResultPreviewModal.tsx`

Responsibilities:

1. Render nothing when no result is selected
2. Render the backdrop and modal surface when open
3. Lock focus on the close action simply enough for this scope
4. Close on `Esc`
5. Close on backdrop click
6. Stop propagation when clicking inside the modal content

## Data Flow

1. `SearchResultsPanel` builds the `videoNameMap` as it already does.
2. Each `ResultCard` receives:
   - `result`
   - `videoName`
   - `onPreview`
3. Clicking the card calls `onPreview(result)`.
4. `SearchResultsPanel` stores that result in `previewResult`.
5. `ResultPreviewModal` receives:
   - `result`
   - `videoName`
   - `onClose`
6. The modal computes the same annotated image URL using the existing helper.

## Styling

All styling can live in `web/src/index.css`.

### Card Updates

The result card should gain:

1. Pointer cursor
2. Clear focus-visible ring
3. Slightly stronger hover and active affordances

### Modal Styles

Add styles for:

1. Full-screen dark translucent backdrop
2. Centered modal panel with rounded corners
3. Large image area with contained scaling
4. Close button positioned clearly in the top-right area
5. Responsive layout that collapses cleanly on narrow screens

The visual style should match the current glassy, clean aesthetic rather than introducing a separate design language.

## Accessibility

1. The result card must be keyboard-focusable.
2. Pressing `Enter` or `Space` on the card should open the preview if the card is implemented as a button.
3. The modal close button must have an accessible label.
4. Pressing `Esc` must close the modal.
5. The backdrop and modal should not trap users in an unreachable state.

This phase does not require a full custom focus trap implementation, but the interaction should still be usable by keyboard.

## Error Handling

1. If the image fails to load, the browser image fallback behavior remains acceptable for this phase.
2. If the result data is missing, the modal should render nothing.
3. If the selected result disappears because a new search replaces results, the modal should close automatically by clearing preview state when results refresh.

## Testing Strategy

This feature should be implemented with frontend component tests only if the current project already has that setup.
If it does not, the minimal verification for this phase is manual browser testing after implementation.

Manual verification should confirm:

1. Clicking a result card opens the modal
2. Clicking outside closes it
3. Pressing `Esc` closes it
4. Mobile-sized layouts still show the image clearly
5. The grid remains unchanged when the modal is closed

## Acceptance Criteria

1. A user can click any result card in the search results grid to open a large preview modal.
2. The modal shows the corresponding annotated frame, video name, and timestamp.
3. The modal closes via close button, backdrop click, and `Esc`.
4. The interaction works on desktop and mobile widths.
5. No backend API or schema changes are required.
