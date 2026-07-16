<script lang="ts">
  // Inline expand skills — one open panel at a time

  type Skill = {
    name: string;
    group: string;
    usage: string;
    image: string;
  };

  let { items = [] }: { items: Skill[] } = $props();
  let open = $state<string | null>(null);

  function toggle(name: string) {
    open = open === name ? null : name;
  }
</script>

<ul class="sk-expand">
  {#each items as item}
    <li class="sk-expand__item" class:is-open={open === item.name}>
      <button
        type="button"
        class="sk-expand__hit"
        aria-expanded={open === item.name}
        onclick={() => toggle(item.name)}
      >
        <span class="sk-expand__meta">
          <span class="sk-expand__group">{item.group}</span>
          <span class="sk-expand__name">{item.name}</span>
        </span>
        <span class="sk-expand__chevron" aria-hidden="true"></span>
      </button>
      {#if open === item.name}
        <div class="sk-expand__panel">
          <img
            class="sk-expand__img"
            src={item.image}
            alt=""
            width="640"
            height="360"
            decoding="async"
            data-no-border
          />
          <p class="sk-expand__usage">{item.usage}</p>
        </div>
      {/if}
    </li>
  {/each}
</ul>

<style>
  .sk-expand {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .sk-expand__item {
    overflow: hidden;
    border-radius: 0.85rem;
    background: #fff;
    box-shadow: 0 1px 0 rgba(17, 50, 75, 0.06);
  }

  .sk-expand__hit {
    display: flex;
    width: 100%;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    border: none;
    background: transparent;
    padding: 1rem 1.1rem;
    text-align: left;
    cursor: pointer;
  }

  .sk-expand__hit:focus-visible {
    outline: 3px solid var(--color-focus);
    outline-offset: -3px;
  }

  .sk-expand__meta {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .sk-expand__group {
    font-family: 'Geist Mono', ui-monospace, monospace;
    font-size: 0.65rem;
    letter-spacing: 0.16em;
    text-transform: uppercase;
    color: #5a6b7a;
  }

  .sk-expand__name {
    font-size: 0.95rem;
    font-weight: 600;
    color: #232e3a;
  }

  .sk-expand__chevron {
    width: 0.55rem;
    height: 0.55rem;
    flex-shrink: 0;
    border-right: 2px solid #108474;
    border-bottom: 2px solid #108474;
    transform: rotate(45deg);
    transition: transform 0.18s ease;
  }

  .sk-expand__item.is-open .sk-expand__chevron {
    transform: rotate(-135deg);
  }

  .sk-expand__panel {
    display: grid;
    gap: 0.85rem;
    border-top: 1px solid #e6ebf0;
    padding: 0 1.1rem 1.1rem;
  }

  @media (min-width: 640px) {
    .sk-expand__panel {
      grid-template-columns: minmax(0, 11rem) minmax(0, 1fr);
      align-items: start;
    }
  }

  .sk-expand__img {
    width: 100%;
    border-radius: 0.5rem;
    background: #0e1a24;
    aspect-ratio: 16 / 9;
    object-fit: contain;
  }

  .sk-expand__usage {
    font-size: 0.88rem;
    line-height: 1.5;
    color: #3a4a58;
  }
</style>
