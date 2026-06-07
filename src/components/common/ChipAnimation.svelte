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
   * - --mobile-scale: narrow-screen zoom (CSS on `.chip-animation`, default 1.85)
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
   *
   * SIGNAL FLOW (current along traces) — tune colors in <style> via CSS vars:
   * - --signal-color: pulse stroke color
   * - --signal-glow: SVG feDropShadow / filter tint
   */
  const VIEWBOX = { x: -158, y: -132, w: 298, h: 248 };

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

  // PCB traces on the board plane (z = 0)
  const pcbTraces: [number, number, number][][] = [
    [
      [X0 + CHIP_W, -6, 0],
      [78, -6, 0],
      [78, -32, 0],
      [86, -32, 0],
    ],
    [
      [X0 + CHIP_W, 10, 0],
      [72, 10, 0],
      [72, 28, 0],
      [84, 28, 0],
    ],
    [
      [X0 + CHIP_W, 0, 0],
      [82, 0, 0],
      [82, -48, 0],
      [88, -48, 0],
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
      [54, Y0 + 10, 0],
      [54, -58, 0],
      [68, -58, 0],
      [68, -74, 0],
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
      [X0 + CHIP_W - 10, 58, 0],
      [48, 58, 0],
      [64, 58, 0],
      [64, 82, 0],
    ],
  ];

  // Vertical traces from the MCU apex toward the navbar (z axis = up on screen)
  const navbarTraces: [number, number, number][][] = [
    [
      [0, 0, 5],
      [0, 0, 40],
      [0, 0, 76],
      [0, 0, 102],
    ],
    [
      [-9, 5, 5],
      [-9, 5, 46],
      [11, 5, 46],
      [11, 5, 96],
    ],
  ];

  const allTraces = [...pcbTraces, ...navbarTraces];

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
  class="chip-animation pointer-events-none absolute inset-0 z-0 w-full bg-black"
  aria-hidden="true"
>
  <svg
    class="chip-animation__svg absolute inset-0 mx-auto h-full w-full lg:inset-y-0 lg:right-0 lg:mx-0 lg:w-[70%] xl:max-w-6xl"
    viewBox={`${VIEWBOX.x} ${VIEWBOX.y} ${VIEWBOX.w} ${VIEWBOX.h}`}
    preserveAspectRatio="xMidYMid meet"
    overflow="visible"
    xmlns="http://www.w3.org/2000/svg"
  >
    <defs>
      <filter id="trace-signal-glow" x="-80%" y="-80%" width="260%" height="260%">
        <!-- Keep flood-color in sync with --signal-glow below -->
        <feDropShadow dx="0" dy="0" stdDeviation="1.8" flood-color="#67e8f9" flood-opacity="0.85" />
      </filter>
    </defs>

    <!-- PCB footprint + static traces (behind the die stack) -->
    <g
      class="trace-base"
      stroke="#ffffff"
      stroke-opacity="0.25"
      fill="none"
      stroke-width="0.9"
      stroke-linejoin="round"
      stroke-linecap="round"
    >
      <polygon points={footprint} stroke-width="1.1" />
      {#each allTraces as points}
        <polyline points={tracePath(points)} />
        {@const [px, py] = padPoint(points)}
        <circle cx={px} cy={py} r="3.2" fill="#ffffff" fill-opacity="0.25" stroke="none" />
      {/each}
    </g>

    <!-- Current pulses along traces (behind the die stack) -->
    <g
      class="trace-signals"
      fill="none"
      stroke-linecap="round"
      stroke-linejoin="round"
      filter="url(#trace-signal-glow)"
    >
      {#each allTraces as points, index}
        <polyline
          points={tracePath(points)}
          class="trace-signal"
          style={`animation-delay: ${(index * 0.11) % 1.8}s`}
        />
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
    overflow: hidden;

    /* Signal flow colors — edit these */
    --signal-color: #22d3ee;
    --signal-glow: #67e8f9; /* also update flood-color in #trace-signal-glow above */

    /* Narrow: sit behind hero copy, faded so text stays readable */
    opacity: 0.38;

    /* Narrow: zoom the chip larger than hero text (traces may clip at edges) */
    --mobile-scale: 1.85;
  }

  @media (min-width: 1024px) {
    .chip-animation {
      opacity: 1;
    }
  }

  .trace-signal {
    stroke: var(--signal-color);
    stroke-width: 1.15;
    stroke-dasharray: 5 16;
    animation: trace-signal-flow 1.7s linear infinite;
  }

  @keyframes trace-signal-flow {
    to {
      stroke-dashoffset: -21;
    }
  }

  @media (prefers-reduced-motion: reduce) {
    .trace-signal {
      animation: none;
      stroke-dasharray: none;
    }
  }

  .chip-animation__svg {
    /* Narrow: centered behind copy, scaled up. Wide (lg+): anchored on the right */
    left: 0;
    right: 0;
    transform: scale(var(--mobile-scale));
    transform-origin: 50% 46%;
  }

  @media (min-width: 1024px) {
    .chip-animation {
      --mobile-scale: 1;
    }

    .chip-animation__svg {
      left: auto;
      right: 0;
      transform: none;
      transform-origin: center;
    }
  }
</style>
