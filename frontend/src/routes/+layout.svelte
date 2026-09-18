<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';
	import { Sun, Moon } from 'lucide-svelte';
	import { onMount } from 'svelte';

	let { children } = $props();
	
	let isDark = $state(false);

	onMount(() => {
		const theme = localStorage.getItem('theme');
		if (theme === 'dim') {
			isDark = true;
		}
	});

	$effect(() => {
		const theme = isDark ? 'dim' : 'light';
		document.documentElement.setAttribute('data-theme', theme);
		localStorage.setItem('theme', theme);
	});
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<div class="min-h-screen flex flex-col bg-base-200">
	<header class="navbar bg-base-100 shadow-sm px-4 lg:px-8 flex justify-between items-center">
		<div class="flex-1">
			<a href="/" class="text-2xl font-black text-primary tracking-tighter flex items-center gap-2">
				<span class="bg-primary text-primary-content px-2 py-1 rounded-lg">Re</span>Cut
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
