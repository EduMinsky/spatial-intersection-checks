# spatial-intersection-checks
Utility functions to identify true polygon intersections in GIS workflows.<br>
<br>
The algorithm works by:

1. Applying spatial predicates to identify candidate intersecting geometries
2. Using configurable buffer operations to validate whether intersections represent
meaningful area overlap rather than boundary or vertex contact
3. Returning only polygons that satisfy the criteria for true spatial intersection
---
### Motivation

Relating geometries is a fundamental task in spatial data analysis and GIS workflows.
This is commonly done using spatial predicates (e.g. `intersects`, `touches`, `overlaps`).
However, relying exclusively on these operations can lead to false positives.

In practice, many detected intersections occur when polygon boundaries merely touch
along edges or at single vertices. These cases do not represent true spatial overlap,
but are often the result of georeferencing inaccuracies or topological artifacts
introduced during polygon creation.

To address this issue, **spatial-intersection-checks** provides a lightweight algorithm
to identify *true* polygon intersections by combining spatial predicates with
buffer-based validation and additional geometric checks.

---
### Packages used:


---
### The Process:
---
### What I learned:
---
### How can it be improved:

