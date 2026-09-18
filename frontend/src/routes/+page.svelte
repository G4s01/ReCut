<script lang="ts">
  import { Scissors, Clock, Link, Music, Video, Download, Play, CircleAlert, CheckCircle } from 'lucide-svelte';
  import favicon from '$lib/assets/favicon.svg';
  import recutLogo from '$lib/assets/ReCut.svg';
  import { env } from '$env/dynamic/public';

  let url = $state('');
  
  let startHours = $state<number | null>(null);
  let startMinutes = $state<number | null>(null);
  let startSeconds = $state<number | null>(null);
  
  let endHours = $state<number | null>(null);
  let endMinutes = $state<number | null>(null);
  let endSeconds = $state<number | null>(null);
  
  let formatType = $state<'video' | 'video_only' | 'audio'>('video');
  let selectedFormat = $state<'mp4' | 'webm' | 'm4a' | 'opus' | 'mp3' | 'wav'>('mp4');

  function setFormatType(type: 'video' | 'video_only' | 'audio') {
    formatType = type;
    if ((type === 'video' || type === 'video_only') && !['mp4', 'webm'].includes(selectedFormat)) selectedFormat = 'mp4';
    else if (type === 'audio' && !['m4a', 'opus', 'mp3', 'wav'].includes(selectedFormat)) selectedFormat = 'm4a';
  }

  let loading = $state(false);
  let error = $state('');
  let result = $state<{ file_url: string; filename: string } | null>(null);

  let videoInfo = $state<{duration: number | null, title: string | null} | null>(null);
  let infoLoading = $state(false);
  
  let showHours = $derived(!videoInfo?.duration || videoInfo.duration >= 3600);

  let startSecs = $state(0);
  let endSecs = $state(0);
  let activeThumb = $state<'start'|'end'>('end');

  let apiUrl = env.PUBLIC_API_URL || 'http://localhost:8000';

  let youtubeId = $derived.by(() => {
    if (!url) return null;
    const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?.+&v=))([^&]{11})/);
    return match ? match[1] : null;
  });

  let debounceTimeout: ReturnType<typeof setTimeout> | null = null;
  
  function onUrlInput() {
    if (debounceTimeout) clearTimeout(debounceTimeout);
    
    if (url && (url.startsWith('http://') || url.startsWith('https://'))) {
      debounceTimeout = setTimeout(async () => {
        infoLoading = true;
        error = '';
        try {
          const res = await fetch(`${apiUrl}/api/info`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url })
          });
          if (res.ok) {
            videoInfo = await res.json();
            if (videoInfo?.duration) {
              startSecs = 0;
              endSecs = Math.floor(videoInfo.duration);
              updateFromStartSecs();
              updateFromEndSecs();
            }
          } else {
            videoInfo = null;
            const errData = await res.json().catch(() => null);
            error = errData?.detail || 'Failed to fetch video info. Backend might be unreachable.';
          }
        } catch (e) {
          videoInfo = null;
          error = 'Network error fetching video info.';
        } finally {
          infoLoading = false;
        }
      }, 500);
    } else {
      videoInfo = null;
    }
  }

  function updateFromStartSecs() {
    activeThumb = 'start';
    if (startSecs > endSecs) {
      startSecs = endSecs;
    }
    startHours = Math.floor(startSecs / 3600);
    startMinutes = Math.floor((startSecs % 3600) / 60);
    startSeconds = startSecs % 60;
  }
  function updateFromEndSecs() {
    activeThumb = 'end';
    if (endSecs < startSecs) {
      endSecs = startSecs;
    }
    endHours = Math.floor(endSecs / 3600);
    endMinutes = Math.floor((endSecs % 3600) / 60);
    endSeconds = endSecs % 60;
  }

  function updateFromStartInputs() {
    startSecs = (startHours || 0) * 3600 + (startMinutes || 0) * 60 + (startSeconds || 0);
    if (startSecs > endSecs) {
      startSecs = endSecs;
      updateFromStartSecs(); // Refresh inputs to clamped values
    }
  }
  function updateFromEndInputs() {
    endSecs = (endHours || 0) * 3600 + (endMinutes || 0) * 60 + (endSeconds || 0);
    if (videoInfo?.duration && endSecs > videoInfo.duration) {
      endSecs = Math.floor(videoInfo.duration);
    }
    if (endSecs < startSecs) {
      endSecs = startSecs;
      updateFromEndSecs(); // Refresh inputs to clamped values
    }
  }

  async function handleSubmit(e: Event) {
    e.preventDefault();
    if (!url) return;
    
    let startTime: number | null = null;
    let endTime: number | null = null;

    if (startHours !== null || startMinutes !== null || startSeconds !== null) {
      startTime = (startHours || 0) * 3600 + (startMinutes || 0) * 60 + (startSeconds || 0);
    }
    
    if (endHours !== null || endMinutes !== null || endSeconds !== null) {
      endTime = (endHours || 0) * 3600 + (endMinutes || 0) * 60 + (endSeconds || 0);
    }

    if (startTime !== null && endTime !== null && startTime >= endTime) {
      error = 'Start time must be less than end time.';
      return;
    }
    
    loading = true;
    error = '';
    result = null;

    try {
      const response = await fetch(`${apiUrl}/api/clip`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          url,
          start_time: startTime,
          end_time: endTime,
          media_format: formatType,
          format: selectedFormat
        })
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to generate clip');
      }

      result = await response.json();
    } catch (err: any) {
      error = err.message || 'An error occurred';
    } finally {
      loading = false;
    }
  }
</script>

{#snippet timeInput(label: string, type: 'start' | 'end', updateFn?: () => void)}
  <div class="flex-1 w-full space-y-2">
    <span class="text-xs uppercase font-bold opacity-60 ml-1">{label}</span>
    <div class="flex items-center gap-2">
      <div class="join w-full shadow-sm">
        {#if showHours}
        <input type="number" min="0" 
          value={type === 'start' ? startHours : endHours} 
          oninput={(e) => { 
            const val = e.currentTarget.value ? parseInt(e.currentTarget.value) : null;
            if (type === 'start') startHours = val; else endHours = val;
            if (updateFn) updateFn();
          }} 
          placeholder="hh" class="input input-bordered join-item w-full text-center text-lg font-mono px-1" />
        <span class="btn btn-disabled join-item border-y border-base-300 bg-base-100 px-2">:</span>
        {/if}
        <input type="number" min="0" max="59" 
          value={type === 'start' ? startMinutes : endMinutes} 
          oninput={(e) => { 
            const val = e.currentTarget.value ? parseInt(e.currentTarget.value) : null;
            if (type === 'start') startMinutes = val; else endMinutes = val;
            if (updateFn) updateFn();
          }} 
          placeholder="mm" class="input input-bordered join-item w-full text-center text-lg font-mono px-1" />
        <span class="btn btn-disabled join-item border-y border-base-300 bg-base-100 px-2">:</span>
        <input type="number" min="0" max="59" 
          value={type === 'start' ? startSeconds : endSeconds} 
          oninput={(e) => { 
            const val = e.currentTarget.value ? parseInt(e.currentTarget.value) : null;
            if (type === 'start') startSeconds = val; else endSeconds = val;
            if (updateFn) updateFn();
          }} 
          placeholder="ss" class="input input-bordered join-item w-full text-center text-lg font-mono px-1" />
      </div>
    </div>
  </div>
{/snippet}

<div class="hero min-h-[calc(100vh-5rem)] items-start pt-8 lg:pt-16">
  <div class="hero-content flex-col lg:flex-row gap-10 w-full max-w-6xl items-start justify-center">
    
    <!-- Left Column (Form) -->
    <div class="w-full lg:w-1/2 space-y-6">
      <div class="text-center mb-8">
        <h1 class="mb-4 flex flex-col sm:flex-row justify-center items-center gap-3 sm:gap-4 text-transparent bg-clip-text bg-linear-to-r from-primary to-secondary">
          <!-- <img src={recutLogo} alt="ReCut Logo" class="h-16 sm:h-24 w-auto drop-shadow-md" /> -->
          <span class="text-3xl sm:text-5xl font-extrabold ml-2">Clip any video. Instantly.</span>
        </h1>
      </div>

      <div class="card bg-base-100 shadow-2xl border border-base-200">
        <div class="card-body p-6 md:p-8">
          <form onsubmit={handleSubmit} class="space-y-8">
            <!-- URL Input -->
            <div class="form-control w-full">
              <label class="label font-bold" for="url-input">
                <span class="label-text flex items-center gap-2"><Link size={18}/> URL </span>
                {#if infoLoading}
                  <span class="loading loading-spinner loading-xs text-primary"></span>
                {/if}
              </label>
              <input
                id="url-input"
                type="url"
                bind:value={url}
                oninput={onUrlInput}
                placeholder="https://www.youtube.com/watch?v=..."
                class="input input-lg input-bordered input-primary w-full shadow-inner"
                required
              />
              {#if videoInfo?.title}
                <div class="text-sm mt-2 font-semibold opacity-70">
                  {videoInfo.title}
                </div>
              {/if}
            </div>

            <!-- Time Selector (Minutage) -->
            {#if videoInfo?.duration}
            <div class="bg-base-200 p-6 rounded-2xl shadow-inner space-y-4 animate-in fade-in slide-in-from-top-2 duration-300">
              <div class="flex items-center gap-2 font-bold mb-2">
                <Clock size={18} class="text-secondary" /> 
                <span>TIMELINE ({videoInfo.duration ? Math.floor(videoInfo.duration / 60) + 'm ' + Math.floor(videoInfo.duration % 60) + 's' : 'Optional'})</span>
              </div>
              
              <!-- Slider -->
              <div class="relative w-full h-8 flex items-center my-4">
                <div class="absolute w-full h-2 bg-base-300 rounded-full"></div>
                <div class="absolute h-2 bg-primary opacity-50 rounded-full pointer-events-none" 
                     style="left: {(startSecs / videoInfo.duration) * 100}%; width: {((endSecs - startSecs) / videoInfo.duration) * 100}%;"></div>
                
                <input type="range" min="0" max={videoInfo.duration} bind:value={startSecs} oninput={updateFromStartSecs} 
                       class="custom-range-slider thumb-primary {activeThumb === 'start' ? 'z-20' : 'z-10'}" />
                       
                <input type="range" min="0" max={videoInfo.duration} bind:value={endSecs} oninput={updateFromEndSecs} 
                       class="custom-range-slider thumb-secondary {activeThumb === 'end' ? 'z-20' : 'z-10'}" />
              </div>
              
              <div class="flex flex-col md:flex-row gap-6 justify-between items-center">
                <!-- Start Time -->
                {@render timeInput('Start At', 'start', updateFromStartInputs)}

                <div class="hidden md:flex flex-col justify-center opacity-30 px-2 mt-6">
                  <Scissors size={24} />
                </div>

                <!-- End Time -->
                {@render timeInput('End At', 'end', updateFromEndInputs)}
              </div>
            </div>
            {/if}
            {#if infoLoading}
            <!-- Skeleton Loader for Timeline -->
            <div class="bg-base-200 p-6 rounded-2xl shadow-inner space-y-4">
              <div class="skeleton h-6 w-1/3 mb-4"></div>
              <div class="skeleton h-2 w-full my-4"></div>
              <div class="flex justify-between gap-6">
                <div class="skeleton h-12 w-full"></div>
                <div class="skeleton h-12 w-full"></div>
              </div>
            </div>
            {/if}
            
            {#if url && !videoInfo?.duration && !infoLoading}
            <!-- Fallback Time Selector if no duration available -->
            <div class="bg-base-200 p-6 rounded-2xl shadow-inner space-y-4">
              <div class="flex items-center gap-2 font-bold mb-2">
                <Clock size={18} class="text-secondary" /> 
                <span>Timeline (Optional)</span>
              </div>
              <div class="flex flex-col md:flex-row gap-6 justify-between items-center">
                <!-- Start Time -->
                {@render timeInput('INIZIO', 'start', undefined)}

                <div class="hidden md:flex flex-col justify-center opacity-30 px-2 mt-6">
                  <Scissors size={24} />
                </div>

                <!-- End Time -->
                {@render timeInput('FINE', 'end', undefined)}
              </div>
            </div>
            {/if}

            <!-- Format Switch -->
            <div class="space-y-4">
              <div class="label font-bold">
                <span class="label-text">FORMATO</span>
              </div>
              
              <div class="bg-base-200 p-2 rounded-xl flex flex-col md:flex-row gap-2 w-full">
                <button type="button" class="btn flex-1 {formatType === 'video' ? 'btn-primary shadow-lg' : 'btn-ghost'}" onclick={() => setFormatType('video')}>
                  <Video size={18} /> DUALE
                </button>
                <button type="button" class="btn flex-1 {formatType === 'video_only' ? 'btn-accent shadow-lg' : 'btn-ghost'}" onclick={() => setFormatType('video_only')}>
                  <Video size={18} /> VIDEO
                </button>
                <button type="button" class="btn flex-1 {formatType === 'audio' ? 'btn-secondary shadow-lg' : 'btn-ghost'}" onclick={() => setFormatType('audio')}>
                  <Music size={18} /> AUDIO
                </button>
              </div>

              <!-- Format Reveal -->
              <div class="mt-4 px-2">
                {#if formatType === 'video' || formatType === 'video_only'}
                  <div class="animate-in fade-in slide-in-from-top-2 duration-300 flex flex-wrap gap-4">
                    <label class="cursor-pointer label justify-start gap-3">
                      <input type="radio" name="format-opt-video" class="radio radio-primary" value="mp4" bind:group={selectedFormat} />
                      <span class="label-text font-medium">MP4 (Best Quality)</span>
                    </label>
                    <label class="cursor-pointer label justify-start gap-3">
                      <input type="radio" name="format-opt-video" class="radio radio-primary" value="webm" bind:group={selectedFormat} />
                      <span class="label-text font-medium">WEBM</span>
                    </label>
                  </div>
                {:else}
                  <div class="animate-in fade-in slide-in-from-top-2 duration-300 flex flex-wrap gap-4">
                    <label class="cursor-pointer label justify-start gap-3">
                      <input type="radio" name="format-opt-audio" class="radio radio-secondary" value="m4a" bind:group={selectedFormat} />
                      <span class="label-text font-medium">M4A</span>
                    </label>
                    <label class="cursor-pointer label justify-start gap-3">
                      <input type="radio" name="format-opt-audio" class="radio radio-secondary" value="opus" bind:group={selectedFormat} />
                      <span class="label-text font-medium">OPUS</span>
                    </label>
                    <label class="cursor-pointer label justify-start gap-3">
                      <input type="radio" name="format-opt-audio" class="radio radio-secondary" value="mp3" bind:group={selectedFormat} />
                      <span class="label-text font-medium">MP3</span>
                    </label>
                    <label class="cursor-pointer label justify-start gap-3">
                      <input type="radio" name="format-opt-audio" class="radio radio-secondary" value="wav" bind:group={selectedFormat} />
                      <span class="label-text font-medium">WAV</span>
                    </label>
                  </div>
                {/if}
              </div>
            </div>

            {#if error}
              <div class="alert alert-error text-sm rounded-xl shadow-lg">
                <CircleAlert size={18}/>
                <span>{error}</span>
              </div>
            {/if}

            <div class="w-full {!(loading || !url) ? 'aura aura-rainbow' : ''}">
              <button
                type="submit"
                class="btn btn-lg btn-block {formatType === 'video' ? 'btn-primary' : 'btn-secondary'} rounded-2xl text-lg font-bold shadow-xl hover:-translate-y-1 transition-transform"
                disabled={loading || !url}
              >
                {#if loading}
                  <span class="loading loading-spinner"></span>
                  ATTENDI...
                {:else}
                  <Scissors size={20} class="mr-2"/> CONVERTI
                {/if}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Right Column (Preview / Results) -->
    <div class="w-full lg:w-1/2 space-y-6">
      {#if result && !loading}
        <div class="card bg-success text-success-content shadow-2xl overflow-hidden transform scale-100 animate-in zoom-in-95 duration-300 border-4 border-success-content/20">
          <div class="card-body p-4 md:p-8 flex flex-col justify-center space-y-4">
            
            <!-- Mobile Download Button (Top) -->
            <div class="block lg:hidden w-full mb-2">
              <div class="aura aura-rainbow w-full">
                <a
                  href="{apiUrl}{result.file_url}"
                  download={result.filename}
                  class="btn btn-lg w-full bg-base-100 text-success hover:bg-base-200 border-none shadow-xl text-xl group h-auto py-4"
                >
                  <Download size={28} class="group-hover:scale-110 transition-transform mr-2"/> Download File
                </a>
              </div>
            </div>

            {#if formatType === 'video' || formatType === 'video_only'}
              <div class="rounded-xl overflow-hidden shadow-lg border border-success-content/20 bg-black">
                <video src="{apiUrl}{result.file_url}" controls class="w-full aspect-video" autoplay>
                  <track kind="captions" src="" srclang="en" label="English" default />
                </video>
              </div>
            {:else}
              <div class="p-4 rounded-xl shadow-lg border border-success-content/20 bg-base-100 text-base-content">
                <audio src="{apiUrl}{result.file_url}" controls class="w-full" autoplay></audio>
              </div>
            {/if}

            <!-- Desktop Download Button (Bottom) -->
            <div class="hidden lg:block w-full mt-4">
              <div class="aura aura-rainbow w-full">
                <a
                  href="{apiUrl}{result.file_url}"
                  download={result.filename}
                  class="btn btn-lg w-full bg-base-100 text-success hover:bg-base-200 border-none shadow-xl text-xl group h-auto py-4"
                >
                  <Download size={28} class="group-hover:scale-110 transition-transform mr-2"/> SCARICA
                </a>
              </div>
            </div>

          </div>
        </div>
      {:else if youtubeId}
        <div class="card bg-base-100 shadow-xl border border-base-200 overflow-hidden">
          <div class="card-body p-0">
            <div class="bg-base-300 px-4 py-3 flex items-center gap-2 border-b border-base-200">
              <Play size={16} class="text-primary"/>
              <span class="text-sm font-bold uppercase tracking-wider opacity-70">ANTEPRIMA</span>
            </div>
            <div class="aspect-video w-full bg-black">
              <iframe
                width="100%"
                height="100%"
                src="https://www.youtube.com/embed/{youtubeId}"
                title="YouTube video preview"
                frameborder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                allowfullscreen
              ></iframe>
            </div>
          </div>
        </div>
      {:else}
        <!-- Desktop Empty Placeholder -->
        <div class="hidden lg:flex flex-col items-center justify-center h-[calc(100%-1.5rem)] min-h-100 border-4 border-dashed border-base-300 rounded-3xl opacity-60 bg-base-100/30">
          <Video size={64} class="mb-4 opacity-50 text-base-content" />
          <p class="font-black text-2xl uppercase tracking-widest text-base-content/70">PAREA ANTEPRIMA</p>
          <p class="text-base font-medium opacity-50 mt-2">INCOLLA UN URL PER INIZIARE</p>
        </div>
      {/if}
    </div>
    
  </div>
</div>


