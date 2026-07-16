<script lang="ts">
  // Skills carousel — snap scroll with prev/next

  type Skill = {
    name: string;
    group: string;
    usage: string;
    image: string;
  };

  let { items = [] }: { items: Skill[] } = $props();

  let track: HTMLDivElement | undefined = $state();
  let index = $state(0);

  function scrollTo(i: number) {
    if (!track) return;
    const next = Math.max(0, Math.min(items.length - 1, i));
    index = next;
    const card = track.children[next] as HTMLElement | undefined;
    card?.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
  }

  function onScroll() {
    if (!track) return;
    const mid = track.scrollLeft + track.clientWidth / 2;
    let best = 0;
    let bestDist = Infinity;
    Array.from(track.children).forEach((child, i) => {
      const el = child as HTMLElement;
      const c = el.offsetLeft + el.offsetWidth / 2;
      const d = Math.abs(c - mid);
      if (d < bestDist) {
        bestDist = d;
        best = i;
      }
    });
    index = best;
  }
</script>

<div class="sk-carousel">
  <div class="sk-carousel__toolbar">
    <button type="button" class="sk-carousel__nav" onclick={() => scrollTo(index - 1)} disabled={index === 0} aria-label="Previous skill">
      Prev
    </button>
    <p class="sk-carousel__count">{index + 1} / {items.length}</p>
    <button
      type="button"
      class="sk-carousel__nav"
      onclick={() => scrollTo(index + 1)}
      disabled={index >= items.length - 1}
      aria-label="Next skill"
    >
      Next
    </button>
  </div>

  <div class="sk-carousel__track" bind:this={track} onscroll={onScroll}>
    {#each items as item, i}
      <article class="sk-carousel__card" class:is-active={i === index} aria-current={i === index ? 'true' : undefined}>
        <div class="sk-carousel__media">
          <img src={item.image} alt="" width="640" height="360" decoding="async" data-no-border />
        </div>
        <div class="sk-carousel__body">
          <p class="sk-carousel__group">{item.group}</p>
          <h3 class="sk-carousel__name">{item.name}</h3>
          <p class="sk-carousel__usage">{item.usage}</p>
        </div>
      </article>
    {/each}
  </div>
</div>

<style>
  .sk-carousel {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .sk-carousel__toolbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
  }

  .sk-carousel__count {
    font-family: 'Geist Mono', ui-monospace, monospace;
    font-size: 0.7rem;
    letter-spacing: 0.12em;
    color: var(--color-secondary);
  }

  .sk-carousel__nav {
    border: 1px solid var(--color-border);
    border-radius: 999px;
    background: #fff;
    padding: 0.45rem 1rem;
    font-size: 0.8rem;
    font-weight: 600;
    color: #232e3a;
    cursor: pointer;
  }

  .sk-carousel__nav:disabled {
    opacity: 0.4;
    cursor: default;
  }

  .sk-carousel__nav:not(:disabled):hover {
    border-color: #108474;
  }

  .sk-carousel__track {
    display: flex;
    gap: 1rem;
    overflow-x: auto;
    scroll-snap-type: x mandatory;
    scroll-padding-inline: 1rem;
    padding: 0.25rem 0.15rem 1rem;
    -webkit-overflow-scrolling: touch;
  }

  .sk-carousel__card {
    flex: 0 0 min(88%, 22rem);
    scroll-snap-align: center;
    overflow: hidden;
    border-radius: 1rem;
    background: #fff;
    box-shadow: 0 1px 0 rgba(17, 50, 75, 0.06);
    opacity: 0.55;
    transform: scale(0.96);
    transition:
      opacity 0.2s ease,
      transform 0.2s ease;
  }

  .sk-carousel__card.is-active {
    opacity: 1;
    transform: scale(1);
    box-shadow: 0 10px 28px rgba(17, 50, 75, 0.12);
  }

  .sk-carousel__media {
    background: #0e1a24;
  }

  .sk-carousel__media img {
    display: block;
    width: 100%;
    aspect-ratio: 16 / 9;
    object-fit: contain;
  }

  .sk-carousel__body {
    padding: 1.1rem 1.15rem 1.25rem;
  }

  .sk-carousel__group {
    margin-bottom: 0.35rem;
    font-family: 'Geist Mono', ui-monospace, monospace;
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #5a6b7a;
  }

  .sk-carousel__name {
    margin-bottom: 0.55rem;
    font-size: 1.15rem;
    font-weight: 700;
    color: #232e3a;
  }

  .sk-carousel__usage {
    font-size: 0.85rem;
    line-height: 1.5;
    color: #3a4a58;
  }

  @media (prefers-reduced-motion: reduce) {
    .sk-carousel__card {
      transition: none;
    }
  }
</style>
