<script lang="ts">
  /* eslint-env browser */
  // Isometric stacked-die chip — scroll-driven layer separation (no scroll lock)

  import { onMount } from 'svelte';

  /**
   * Fine-tuning guide — all layout/animation knobs live here and on the SVG below.
   *
   * DISPLAY (how big / where on screen)
   * - VIEWBOX: smaller `w`/`h` zooms in; adjust `x`/`y` to pan (move chip right = decrease `x`)
   * - SVG panel width: Tailwind classes on `.chip-animation__svg` (w-[…], max-w-…)
   *
   * GEOMETRY (chip + PCB in isometric units)
   * - CHIP_W / CHIP_D: footprint and die layer size
   * - LAYER_H / LAYER_GAP: slab thickness and gap when expanded
   * - `traces` array: Manhattan routes and pad positions (add entries / extend coords for more/longer traces)
   *
   * ANIMATION (scroll-driven stack)
   * - SCROLL_RANGE: px of page scroll mapped to full progress (0→1)
   * - SEPARATION_PX: how far each layer rises at progress = 1
   * - STAGGER: delay between layers (0–1 progress units per layer index)
   * - LAYER_COUNT: number of stacked slabs
   */
  const VIEWBOX = { x: -142, y: -118, w: 218, h: 218 };

  const SCROLL_RANGE = 400;
  const LAYER_COUNT = 7;
  const SEPARATION_PX = 16;
  const STAGGER = 0.09;

  // Chip dimensions in isometric units
  const CHIP_W = 58;
  const CHIP_D = 58;
  const LAYER_H = 3.5;
  const LAYER_GAP = 1.2;
  const X0 = -CHIP_W / 2;
  const Y0 = -CHIP_D / 2;

  const COS30 = Math.cos(Math.PI / 6);
  const SIN30 = Math.sin(Math.PI / 6);

  let progress = $state(0);

  function clamp(value: number, min: number, max: number): number {
    return Math.min(max, Math.max(min, value));
  }

  function scrollToProgress(scrollY: number): number {
    return clamp(scrollY / SCROLL_RANGE, 0, 1);
  }

  /** Vertical offset per layer — staggered rise as scroll progress increases */
  function layerOffset(index: number, p: number): number {
    const staggerFactor = 1 + index * 0.06;
    const start = index * STAGGER;
    const denom = Math.max(1 - (LAYER_COUNT - 1) * STAGGER, 0.01);
    const local = clamp((p - start) / denom, 0, 1);
    return local * (index + 1) * SEPARATION_PX * staggerFactor;
  }

  function iso(x: number, y: number, z: number): [number, number] {
    return [(x - y) * COS30, (x + y) * SIN30 - z];
  }

  function pt(x: number, y: number, z: number): string {
    const [sx, sy] = iso(x, y, z);
    return `${sx.toFixed(2)},${sy.toFixed(2)}`;
  }

  function poly(points: [number, number, number][]): string {
    return points.map(([x, y, z]) => pt(x, y, z)).join(' ');
  }

  /** Top / left / right faces of a thin isometric slab */
  function layerFaces(baseZ: number) {
    const topZ = baseZ + LAYER_H;
    return {
      top: poly([
        [X0, Y0, topZ],
        [X0 + CHIP_W, Y0, topZ],
        [X0 + CHIP_W, Y0 + CHIP_D, topZ],
        [X0, Y0 + CHIP_D, topZ],
      ]),
      left: poly([
        [X0, Y0 + CHIP_D, baseZ],
        [X0 + CHIP_W, Y0 + CHIP_D, baseZ],
        [X0 + CHIP_W, Y0 + CHIP_D, topZ],
        [X0, Y0 + CHIP_D, topZ],
      ]),
      right: poly([
        [X0 + CHIP_W, Y0, baseZ],
        [X0 + CHIP_W, Y0 + CHIP_D, baseZ],
        [X0 + CHIP_W, Y0 + CHIP_D, topZ],
        [X0 + CHIP_W, Y0, topZ],
      ]),
    };
  }

  // PCB traces: Manhattan routes from footprint — edit coords here for length/count
  const traces: [number, number, number][][] = [
    // East
    [
      [X0 + CHIP_W, -6, 0],
      [84, -6, 0],
      [84, -32, 0],
      [96, -32, 0],
    ],
    [
      [X0 + CHIP_W, 10, 0],
      [78, 10, 0],
      [78, 28, 0],
      [94, 28, 0],
    ],
    [
      [X0 + CHIP_W, 0, 0],
      [92, 0, 0],
      [92, -48, 0],
      [98, -48, 0],
    ],
    // North
    [
      [-10, Y0, 0],
      [-10, -76, 0],
      [24, -76, 0],
      [24, -92, 0],
    ],
    [
      [12, Y0, 0],
      [12, -68, 0],
      [-38, -68, 0],
      [-38, -88, 0],
    ],
    [
      [0, Y0, 0],
      [0, -88, 0],
      [-26, -88, 0],
      [-26, -96, 0],
    ],
    // West
    [
      [X0, -10, 0],
      [-80, -10, 0],
      [-80, -36, 0],
      [-96, -36, 0],
    ],
    [
      [X0, 8, 0],
      [-74, 8, 0],
      [-74, 32, 0],
      [-92, 32, 0],
    ],
    [
      [X0, 0, 0],
      [-90, 0, 0],
      [-90, 26, 0],
      [-98, 26, 0],
    ],
    // South
    [
      [10, Y0 + CHIP_D, 0],
      [10, 76, 0],
      [40, 76, 0],
      [40, 94, 0],
    ],
    [
      [-8, Y0 + CHIP_D, 0],
      [-8, 82, 0],
      [-36, 82, 0],
      [-36, 96, 0],
    ],
    [
      [0, Y0 + CHIP_D, 0],
      [0, 90, 0],
      [28, 90, 0],
      [28, 98, 0],
    ],
    // NE / NW (extra spokes)
    [
      [X0 + CHIP_W, Y0 + 10, 0],
      [58, Y0 + 10, 0],
      [58, -58, 0],
      [76, -58, 0],
      [76, -78, 0],
    ],
    [
      [X0 + 10, Y0, 0],
      [X0 + 10, -58, 0],
      [-46, -58, 0],
      [-46, -78, 0],
    ],
    // SW / SE (extra spokes)
    [
      [X0, Y0 + CHIP_D - 10, 0],
      [-56, Y0 + CHIP_D - 10, 0],
      [-56, 72, 0],
      [-78, 72, 0],
      [-78, 92, 0],
    ],
    [
      [X0 + CHIP_W - 10, Y0 + CHIP_D, 0],
      [X0 + CHIP_W - 10, 62, 0],
      [52, 62, 0],
      [72, 62, 0],
      [72, 88, 0],
    ],
  ];

  const footprint = poly([
    [X0, Y0, 0],
    [X0 + CHIP_W, Y0, 0],
    [X0 + CHIP_W, Y0 + CHIP_D, 0],
    [X0, Y0 + CHIP_D, 0],
  ]);

  function tracePath(points: [number, number, number][]): string {
    return points.map(([x, y, z]) => pt(x, y, z)).join(' ');
  }

  function padPoint(points: [number, number, number][]): [number, number] {
    const last = points[points.length - 1];
    return iso(last[0], last[1], last[2]);
  }

  const layers = $derived(
    Array.from({ length: LAYER_COUNT }, (_, index) => {
      const baseZ = layerOffset(index, progress) + index * LAYER_GAP * progress;
      return { index, ...layerFaces(baseZ) };
    }),
  );

  onMount(() => {
    const handleScroll = () => {
      progress = scrollToProgress(window.scrollY);
    };

    handleScroll();
    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
    };
  });
</script>

<div
  class="chip-animation pointer-events-none relative h-[100dvh] w-full bg-black"
  aria-hidden="true"
>
  <svg
    class="chip-animation__svg absolute inset-y-0 right-0 h-full w-[92%] sm:w-[80%] lg:w-[70%] xl:max-w-6xl"
    viewBox={`${VIEWBOX.x} ${VIEWBOX.y} ${VIEWBOX.w} ${VIEWBOX.h}`}
    preserveAspectRatio="xMidYMid meet"
    xmlns="http://www.w3.org/2000/svg"
  >
    <!-- Static isometric PCB: footprint, traces, pads -->
    <g stroke="#ffffff" stroke-opacity="0.25" fill="none" stroke-width="0.9" stroke-linejoin="round" stroke-linecap="round">
      <polygon points={footprint} stroke-width="1.1" />
      {#each traces as points}
        <polyline points={tracePath(points)} />
        {@const [px, py] = padPoint(points)}
        <circle cx={px} cy={py} r="3.2" fill="#ffffff" fill-opacity="0.25" stroke="none" />
      {/each}
    </g>

    <!-- Stacked die layers (scroll-driven vertical separation) -->
    {#each layers as layer (layer.index)}
      <g>
        <polygon points={layer.right} fill="#b8b8b8" stroke="#888888" stroke-width="0.25" />
        <polygon points={layer.left} fill="#a0a0a0" stroke="#787878" stroke-width="0.25" />
        <polygon points={layer.top} fill="#e0e0e0" stroke="#cccccc" stroke-width="0.25" />
      </g>
    {/each}
  </svg>
</div>

<style>
  .chip-animation {
    /* Never block page scroll or capture clicks */
    pointer-events: none;
    touch-action: pan-y;
  }

  .chip-animation__svg {
    /* Panel width: increase w-[…] / max-w-… to enlarge; decrease x in VIEWBOX to shift right */
    left: auto;
  }
</style>
