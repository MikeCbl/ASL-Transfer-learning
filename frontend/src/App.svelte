<script lang="ts">
  type Top = { class: string; confidence: number };
  type Prediction = {
    predicted: string; confidence: number; top3: Top[];
    model: string; quantized: boolean;
  };
  type CompareRow = {
    model: string; quantized: boolean;
    predicted: string; confidence: number; latency_ms: number;
  };

  const MODELS = [
    { id: "mobilenetv2", label: "MobileNetV2" },
    { id: "resnet18", label: "ResNet18" },
  ];

  let fileInput: HTMLInputElement;
  let file = $state<File | null>(null);
  let preview = $state<string | null>(null);
  let model = $state("mobilenetv2");
  let quantized = $state(false);
  let loading = $state(false);
  let comparing = $state(false);
  let dragging = $state(false);
  let error = $state<string | null>(null);
  let result = $state<Prediction | null>(null);
  let compare = $state<CompareRow[] | null>(null);

  function setFile(f: File | null) {
    file = f; result = null; compare = null; error = null;
    if (preview) URL.revokeObjectURL(preview);
    preview = f ? URL.createObjectURL(f) : null;
  }
  function openPicker() {
    fileInput.value = "";
    fileInput.click();
  }
  function onInput(e: Event) {
    setFile((e.target as HTMLInputElement).files?.[0] ?? null);
  }
  function onDrop(e: DragEvent) {
    e.preventDefault(); dragging = false;
    setFile(e.dataTransfer?.files?.[0] ?? null);
  }

  async function post<T>(url: string, form: FormData): Promise<T> {
    const res = await fetch(url, { method: "POST", body: form });
    if (!res.ok) {
      const d = await res.json().catch(() => ({}));
      throw new Error(d.detail ?? `Błąd ${res.status}`);
    }
    return res.json();
  }

  async function submit() {
    if (!file) return;
    loading = true; error = null; result = null; compare = null;
    try {
      const form = new FormData();
      form.append("file", file);
      form.append("model", model);
      form.append("quantized", String(quantized));
      result = await post<Prediction>("/api/predict", form);
    } catch (e) {
      error = e instanceof Error ? e.message : "Nieznany błąd";
    } finally {
      loading = false;
    }
  }

  async function compareAll() {
    if (!file) return;
    comparing = true; error = null; result = null; compare = null;
    try {
      const form = new FormData();
      form.append("file", file);
      const data = await post<{ results: CompareRow[] }>("/api/compare", form);
      compare = data.results;
    } catch (e) {
      error = e instanceof Error ? e.message : "Nieznany błąd";
    } finally {
      comparing = false;
    }
  }
</script>

<div class="min-h-screen bg-gradient-to-b from-stone-100 to-stone-200 text-stone-900">
  <div class="mx-auto max-w-5xl px-6 py-12">
    <header class="mb-10">
      <p class="text-xs font-bold tracking-[0.2em] text-amber-700 uppercase">transfer learning · onnx</p>
      <h1 class="mt-2 text-5xl font-black tracking-tight sm:text-6xl">
        Alfabet <span class="text-amber-600">migowy</span>
      </h1>
      <p class="mt-3 max-w-prose text-stone-600">
        Wgraj zdjęcie dłoni — model rozpozna literę alfabetu ASL.
      </p>
    </header>

    <div class="grid gap-6 md:grid-cols-2">
      <section class="rounded-2xl border border-stone-300 bg-white/70 p-5 shadow-sm backdrop-blur">
        <div class="mb-4 flex flex-wrap items-center justify-between gap-3">
          <div class="inline-flex rounded-full border border-stone-300 bg-stone-100 p-1">
            {#each MODELS as m}
              <button
                type="button"
                class="cursor-pointer rounded-full px-4 py-1.5 text-sm font-semibold transition {model === m.id
                  ? 'bg-stone-900 text-white shadow'
                  : 'text-stone-600 hover:bg-stone-200 hover:text-stone-900'}"
                onclick={() => (model = m.id)}>{m.label}</button>
            {/each}
          </div>
          <button
            type="button"
            class="inline-flex cursor-pointer items-center gap-2 text-sm font-medium select-none"
            onclick={() => (quantized = !quantized)}
            aria-pressed={quantized}>
            <span class="relative h-6 w-11 rounded-full transition {quantized ? 'bg-amber-500' : 'bg-stone-300'}">
              <span class="absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition {quantized ? 'translate-x-5' : ''}"></span>
            </span>
            INT8
          </button>
        </div>

        <button
          type="button"
          class="flex min-h-56 w-full cursor-pointer flex-col items-center justify-center overflow-hidden rounded-xl border-2 border-dashed transition {dragging
            ? 'border-amber-500 bg-amber-50'
            : 'border-stone-300 bg-stone-50 hover:border-amber-400 hover:bg-stone-100'}"
          ondragover={(e) => { e.preventDefault(); dragging = true; }}
          ondragleave={() => (dragging = false)}
          ondrop={onDrop}
          onclick={openPicker}>
          {#if preview}
            <img src={preview} alt="podgląd" class="max-h-72 w-full object-contain" />
          {:else}
            <div class="text-center text-stone-500">
              <div class="text-4xl text-amber-600">+</div>
              <p class="mt-2">Przeciągnij zdjęcie albo <span class="underline">kliknij</span></p>
              <p class="text-xs">JPG · PNG · WEBP · do 10 MB</p>
            </div>
          {/if}
        </button>
        <input bind:this={fileInput} type="file" accept="image/*" class="hidden" onchange={onInput} />

        {#if preview}
          <div class="mt-2 flex gap-2 text-sm">
            <button
              type="button"
              class="cursor-pointer rounded-lg border border-stone-300 px-3 py-1.5 font-medium transition hover:bg-stone-100"
              onclick={openPicker}>Zmień zdjęcie</button>
            <button
              type="button"
              class="cursor-pointer rounded-lg border border-stone-300 px-3 py-1.5 font-medium text-stone-600 transition hover:bg-red-50 hover:text-red-700"
              onclick={() => setFile(null)}>Usuń</button>
          </div>
        {/if}

        <div class="mt-4 grid grid-cols-2 gap-2">
          <button
            type="button"
            class="cursor-pointer rounded-xl bg-amber-600 py-3 font-bold text-white shadow-sm transition hover:bg-amber-700 hover:shadow-md active:scale-[.99] disabled:cursor-not-allowed disabled:opacity-40"
            onclick={submit} disabled={!file || loading || comparing}>
            {loading ? "Rozpoznaję…" : "Rozpoznaj literę"}
          </button>
          <button
            type="button"
            class="cursor-pointer rounded-xl border border-stone-300 bg-white py-3 font-bold text-stone-800 transition hover:bg-stone-100 active:scale-[.99] disabled:cursor-not-allowed disabled:opacity-40"
            onclick={compareAll} disabled={!file || loading || comparing}>
            {comparing ? "Liczę…" : "Porównaj modele"}
          </button>
        </div>

        {#if error}
          <p class="mt-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>
        {/if}
      </section>

      <section class="flex items-center rounded-2xl border border-stone-300 bg-white/70 p-5 shadow-sm backdrop-blur">
        {#if compare}
          <div class="w-full">
            <h2 class="mb-3 text-sm font-bold tracking-wide text-stone-500 uppercase">Porównanie modeli</h2>
            <table class="w-full text-sm">
              <thead>
                <tr class="border-b border-stone-200 text-left text-stone-500">
                  <th class="py-2 font-medium">Model</th>
                  <th class="py-2 font-medium">INT8</th>
                  <th class="py-2 font-medium">Litera</th>
                  <th class="py-2 text-right font-medium">Pewność</th>
                  <th class="py-2 text-right font-medium">Czas</th>
                </tr>
              </thead>
              <tbody>
                {#each compare as r}
                  <tr class="border-b border-stone-100">
                    <td class="py-2 font-semibold">{r.model}</td>
                    <td class="py-2 text-stone-500">{r.quantized ? "tak" : "–"}</td>
                    <td class="py-2 text-lg font-black">{r.predicted}</td>
                    <td class="py-2 text-right tabular-nums">{(r.confidence * 100).toFixed(1)}%</td>
                    <td class="py-2 text-right tabular-nums text-stone-500">{r.latency_ms} ms</td>
                  </tr>
                {/each}
              </tbody>
            </table>
            <p class="mt-3 text-xs text-stone-400">Czas = sama inferencja ONNX Runtime (CPU), bez preprocessingu.</p>
          </div>
        {:else if result}
          <div class="w-full">
            <div class="text-center text-8xl font-black tracking-tight">{result.predicted}</div>
            <p class="mt-1 text-center text-stone-600">
              pewność <b>{(result.confidence * 100).toFixed(1)}%</b>
              <span class="ml-2 rounded-full bg-stone-900 px-2.5 py-0.5 text-xs font-bold text-white">
                {result.model}{result.quantized ? " · INT8" : ""}
              </span>
            </p>
            <ul class="mt-6 space-y-2">
              {#each result.top3 as t}
                <li class="grid grid-cols-[2rem_1fr_3.5rem] items-center gap-3">
                  <span class="font-bold">{t.class}</span>
                  <span class="h-2.5 overflow-hidden rounded-full bg-stone-200">
                    <span class="block h-full rounded-full bg-gradient-to-r from-amber-500 to-amber-600" style="width:{t.confidence * 100}%"></span>
                  </span>
                  <span class="text-right text-sm text-stone-600 tabular-nums">{(t.confidence * 100).toFixed(1)}%</span>
                </li>
              {/each}
            </ul>
          </div>
        {:else}
          <p class="w-full text-center text-stone-400">Wynik pojawi się tutaj.</p>
        {/if}
      </section>
    </div>
  </div>
</div>