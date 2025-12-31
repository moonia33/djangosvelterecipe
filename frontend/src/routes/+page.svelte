<script lang="ts">
	import { appConfig } from '$lib';

	const highlights = [
		{
			title: 'Aiškus domeno modelis',
			description:
				'Receptai, ingredientai, kategorijos ir žymos dokumentuojami vienoje vietoje, kad API naudotojams nekiltų interpretacijų.',
			badge: 'Model layer'
		},
		{
			title: 'Hybrid paieška',
			description:
				'Klasikinės filtracijos ir semantinių embeddingų derinys leis surasti receptus pagal skonį, nuotaiką ar mitybos tikslus.',
			badge: 'Search'
		},
		{
			title: 'Media ir optimizacija',
			description:
				'Hetzner S3 + WEBP variantai garantuos greitą vaizdų pateikimą bet kuriame įrenginyje.',
			badge: 'Media pipeline'
		}
	];

	const roadmap = [
		{
			title: 'Django + Ninja API',
			description:
				'Struktūruotas routerių sluoksnis su aiškiomis schemomis ir „ownership“ taisyklėmis.',
			status: 'Vystoma'
		},
		{
			title: 'SvelteKit sąsaja',
			description: 'Atskirtas frontend, pasiruošęs naudoti hibridinę paiešką ir personalizaciją.',
			status: 'Planavimas'
		},
		{
			title: 'Media pipeline',
			description: 'Automatiniai WEBP/thumbnail variantai, pasiruošę CDN sluoksniui.',
			status: 'Greitai'
		}
	];

	const apiPreview = `${appConfig.apiBaseUrl.replace(/\/$/, '')}/recipes`;
</script>

<svelte:head>
	<title>Receptų platforma • Modernus Django + Svelte startas</title>
	<meta
		name="description"
		content="API-first receptų platformos karkasas su Django Ninja backend ir SvelteKit frontend."
	/>
</svelte:head>

<main class="landing">
	<section class="hero">
		<div class="hero__content">
			<p class="eyebrow">Django 5 · Ninja · SvelteKit</p>
			<h1>
				Ilgalaikė receptų platforma
				<span>be kompromisų</span>
			</h1>
			<p class="lede">
				API-first monolitas su aiškiu domeno modeliu, pasiruošęs paieškai, personalizacijai ir media
				pipeline išplėtimams.
			</p>
			<div class="hero__cta">
				<a
					class="btn btn--primary"
					href="https://github.com/moonia33/djangosvelterecipe"
					target="_blank"
					rel="noreferrer"
				>
					Žiūrėti repo
				</a>
				<a class="btn btn--ghost" href="mailto:ramunas@inultimo.lt">Susisiekti dėl integracijos</a>
			</div>
		</div>
		<div class="hero__panel">
			<div class="panel__header">
				<span>Pagrindiniai endpointai</span>
				<strong>API</strong>
			</div>
			<div class="panel__body">
				<p>
					<small>Bazinis kelias</small>
					<br />
					<span class="mono">{appConfig.apiBaseUrl}</span>
				</p>
				<p>
					<small>Receptų kolekcija</small>
					<br />
					<span class="mono">GET {apiPreview}</span>
				</p>
				<p>
					<small>Media</small>
					<br />
					<span class="mono">{appConfig.mediaBaseUrl}</span>
				</p>
			</div>
			<div class="panel__footer">
				<span>Statinė analizė · Testai · Paieška</span>
			</div>
		</div>
	</section>

	<section class="grid">
		{#each highlights as highlight}
			<article class="card">
				<span class="badge">{highlight.badge}</span>
				<h3>{highlight.title}</h3>
				<p>{highlight.description}</p>
			</article>
		{/each}
	</section>

	<section class="roadmap">
		<div class="roadmap__title">
			<h2>Kelias į pilną produktą</h2>
			<p>
				Technologinis pamatas jau vietoje – belieka iteruoti API schemas ir sujungti su paieškos bei
				media sluoksniais.
			</p>
		</div>
		<ul>
			{#each roadmap as item}
				<li>
					<div>
						<strong>{item.title}</strong>
						<span>{item.status}</span>
					</div>
					<p>{item.description}</p>
				</li>
			{/each}
		</ul>
	</section>
</main>

<style>
	.landing {
		padding: clamp(2rem, 5vw, 4rem);
		max-width: 1200px;
		margin: 0 auto;
		display: flex;
		flex-direction: column;
		gap: 3rem;
	}

	.hero {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
		gap: 2rem;
		align-items: center;
	}

	.hero__content h1 {
		font-size: clamp(2.5rem, 5vw, 3.6rem);
		line-height: 1.1;
	}

	.hero__content h1 span {
		color: var(--accent);
	}

	.eyebrow {
		text-transform: uppercase;
		letter-spacing: 0.2em;
		font-size: 0.75rem;
		color: var(--muted);
	}

	.lede {
		margin-top: 1rem;
		font-size: 1.1rem;
		color: var(--muted);
	}

	.hero__cta {
		margin-top: 1.75rem;
		display: flex;
		flex-wrap: wrap;
		gap: 1rem;
	}

	.btn {
		padding: 0.85rem 1.5rem;
		border-radius: 999px;
		border: 1px solid transparent;
		font-weight: 600;
		text-decoration: none;
		transition:
			transform 200ms ease,
			border-color 200ms ease,
			background 200ms ease;
	}

	.btn--primary {
		background: linear-gradient(120deg, var(--accent), var(--accent-2));
		color: #050608;
	}

	.btn--ghost {
		border-color: var(--surface-strong);
		color: var(--text);
	}

	.btn:hover {
		transform: translateY(-2px);
	}

	.hero__panel {
		background: var(--surface);
		border: 1px solid var(--surface-strong);
		border-radius: 1.5rem;
		overflow: hidden;
		box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
	}

	.panel__header,
	.panel__footer {
		padding: 1rem 1.5rem;
		display: flex;
		justify-content: space-between;
		align-items: center;
		background: rgba(255, 255, 255, 0.05);
	}

	.panel__body {
		padding: 1.5rem;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.panel__body small {
		color: var(--muted);
		text-transform: uppercase;
		font-size: 0.7rem;
		letter-spacing: 0.1em;
	}

	.mono {
		font-family: 'JetBrains Mono', 'Space Grotesk', monospace;
		font-size: 0.95rem;
		word-break: break-all;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
		gap: 1.5rem;
	}

	.card {
		background: var(--surface);
		border: 1px solid var(--surface-strong);
		border-radius: 1.25rem;
		padding: 1.5rem;
		position: relative;
	}

	.badge {
		position: absolute;
		top: 1.25rem;
		right: 1.25rem;
		font-size: 0.7rem;
		text-transform: uppercase;
		letter-spacing: 0.1em;
		color: var(--accent);
	}

	.card h3 {
		margin-bottom: 0.75rem;
	}

	.card p {
		color: var(--muted);
	}

	.roadmap {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 1.5rem;
		align-items: start;
	}

	.roadmap__title p {
		color: var(--muted);
		margin-top: 0.5rem;
	}

	.roadmap ul {
		list-style: none;
		display: flex;
		flex-direction: column;
		gap: 1rem;
	}

	.roadmap li {
		padding: 1.25rem;
		border-radius: 1rem;
		background: var(--surface);
		border: 1px solid var(--surface-strong);
	}

	.roadmap li div {
		display: flex;
		justify-content: space-between;
		font-size: 0.95rem;
	}

	.roadmap li span {
		color: var(--accent);
		font-weight: 600;
	}

	.roadmap li p {
		margin-top: 0.6rem;
		color: var(--muted);
		font-size: 0.95rem;
	}

	@media (max-width: 600px) {
		.hero__cta {
			flex-direction: column;
		}
	}
</style>
