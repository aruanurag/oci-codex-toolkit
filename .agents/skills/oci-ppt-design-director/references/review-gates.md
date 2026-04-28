# Review Gates

Use this file before sign-off or when iterating on a generated deck.

## Gate 1: Story And Visual Fit

Check:

- does each slide have one visible takeaway
- does the visual style match the audience
- is the architecture slide integrated with the rest of the deck
- does the deck rhythm feel deliberate instead of repetitive

## Gate 2: Geometry And Readability

Reject the deck if you see:

- clipped text
- overlapping boxes
- card bodies spilling beyond their containers
- any text shrinking or wrapping so badly that it visibly escapes the intended card, chip, callout, or summary strip
- any text that only passes by shrinking down to a cramped minimum size
- long single-line copy overrunning a wide horizontal bar or summary strip
- eyebrow pills or labels wrapping awkwardly
- eyebrow, chip, or section labels that wrap, clip, or visually escape their container
- compact icon tiles that combine a service name and explanatory copy so the text crowds the card boundary
- captions touching borders
- unrelated elements colliding

Shorten copy before shrinking fonts into clutter.

## Gate 3: Customer-Safe Content

Reject the deck if you see:

- visible presenter notes
- author prompts
- process language such as draft instructions or internal reminders
- subtitle, footer, summary-strip, or bottom-band text that reads like speaker notes, teaching cues, transitions, or presenter-only interpretation
- inherited internal-only labels that should not ship

Speaker notes may exist separately, but they must not leak onto the visible slide canvas.

## Gate 4: Architecture Slide Craft

Reject the slide if you see:

- connector labels on top of connector lanes
- callout cards crowding the diagram
- OCI icons that render blank, clipped, or detached from their labels
- mismatched spacing between architecture containers and the deck’s other slides
- a technically correct diagram that still looks sparse, unbalanced, or obviously machine-laid-out

## Gate 5: PowerPoint-Native Integrity

Confirm:

- the `.pptx` opens without a repair prompt
- PowerPoint-native export still works
- no presenter notes or author prompts are visible on the slide canvas
- any `ppt/notesSlides/` parts are intentional, valid, and contain presenter-only notes rather than leaked slide content

If PowerPoint export depends on keeping a `notesMaster` or real presenter notes, that is acceptable. The blocker is visible note leakage, broken notes packaging, or presenter notes masquerading as slide content.

## Gate 6: Final Sign-off

The deck is ready only when:

- the message is explicit
- the slides feel calm and intentional
- the deck is editable
- the rendered PowerPoint behaves like a normal customer-facing file
- no visible text escapes its intended container, and any renderer `text-overflow` or `text-cramped` findings have been fixed or the slide has been redesigned
