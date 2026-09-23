<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import recutLogo from '$lib/assets/ReCut.svg';
	import { Sun, Moon } from 'lucide-svelte';
	import { onMount } from 'svelte';

	let { children } = $props();
	
	let isDark = $state(false);

	onMount(() => {
		const theme = localStorage.getItem('theme');
		if (theme === 'recut-dark') {
			isDark = true;
		}
	});

	$effect(() => {
		const theme = isDark ? 'recut-dark' : 'light';
		document.documentElement.setAttribute('data-theme', theme);
		localStorage.setItem('theme', theme);
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="min-h-screen flex flex-col bg-base-200">
	<header class="navbar bg-base-100 shadow-sm px-4 lg:px-8 flex justify-between items-center">
		<div class="flex-1">
			<a href="/" data-sveltekit-reload class="flex items-center">
				<img src={recutLogo} alt="ReCut Logo" class="h-6 md:h-8 w-auto drop-shadow-[0_0_12px_rgba(255,255,255,0.7)]" />
			</a>
		</div>
		<div class="flex-none">
			<label class="swap swap-rotate btn btn-ghost btn-circle">
				<input type="checkbox" bind:checked={isDark} />
				<Sun class="swap-off w-6 h-6" />
				<Moon class="swap-on w-6 h-6" />
			</label>
		</div>
	</header>
	
	<main class="grow w-full max-w-6xl mx-auto p-4 lg:p-8">
		{@render children()}
	</main>
</div>
