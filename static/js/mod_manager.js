document.addEventListener("DOMContentLoaded", async () => {
  const listEl = document.getElementById("mod-list");
  const detailEl = document.getElementById("mod-detail");
  const searchInput = document.getElementById("search-input");
  const filterSelect = document.getElementById("filter-select");
  const sortSelect = document.getElementById("sort-select");
  const exportEnabledBtn = document.getElementById("export-enabled");

  let mods = [], selectedMod = null;
  const rowElements = new Map();

  function safeText(text, fallback = "") {
    return text || fallback;
  }

  function bbcodeToHtml(text) {
  return text
    .replace(/\[b\](.*?)\[\/b\]/gi, "<strong>$1</strong>")
    .replace(/\[i\](.*?)\[\/i\]/gi, "<em>$1</em>")
    .replace(/\[u\](.*?)\[\/u\]/gi, "<u>$1</u>")
    .replace(/\[h1\](.*?)\[\/h1\]/gi, '<h1 class="text-2xl font-bold mt-4 mb-2">$1</h1>')
    .replace(/\[h2\](.*?)\[\/h2\]/gi, '<h2 class="text-xl font-semibold mt-4 mb-2">$1</h2>')
    .replace(/\[h3\](.*?)\[\/h3\]/gi, '<h3 class="text-lg font-medium mt-4 mb-2">$1</h3>')
    .replace(/\[url=(.*?)\](.*?)\[\/url\]/gi, '<a href="$1" target="_blank" class="text-blue-400 underline">$2</a>')
    .replace(/\[img\](.*?)\[\/img\]/gi, '<img src="$1" class="my-2 max-h-40 rounded border border-gray-600" />')
    .replace(/\[list\](.*?)\[\/list\]/gis, (_, inner) => {
      const items = inner.split(/\[\*\]/).filter(Boolean);
      return `<ul class="list-disc pl-6 space-y-1">${items.map(item => `<li>${item.trim()}</li>`).join("")}</ul>`;
    })
    .replace(/\[quote=([^\]]+)\](.*?)\[\/quote\]/gis, '<blockquote class="border-l-4 border-gray-500 pl-4 my-2"><strong>$1:</strong> $2</blockquote>');
}

  try {
    mods = await (await fetch("/api/mods")).json();
    mods.forEach(m => {
      m.favorite = false;
      m.hidden = false;
      m.title = safeText(m.title, 'Untitled');
      m.preview = safeText(m.preview, 'https://placehold.co/100x100');
      m.description = safeText(m.description, '');
      m.updated = safeText(m.updated, 'Unknown');
      m.id = m.id || `mod-${Math.random().toString(36).slice(2)}`;
    });
  } catch (e) {
    listEl.innerHTML = `<div class="text-red-500">Failed to load mods!</div>`;
    console.error("Mod loading error:", e);
    return;
  }

  function highlightTerm(text, term) {
    if (!term) return text;
    const regex = new RegExp(`(${term.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, "gi");
    return text.replace(regex, '<span class="bg-yellow-300 text-black">$1</span>');
  }

  function renderList() {
    listEl.innerHTML = "";
    rowElements.clear();

    let filtered = mods.filter(m => {
      switch (filterSelect.value) {
        case "enabled": return m.enabled;
        case "disabled": return !m.enabled;
        case "favorite": return m.favorite;
        case "hidden": return m.hidden;
        default: return true;
      }
    });

    filtered = filtered.filter(m => m.title.toLowerCase().includes(searchInput.value.toLowerCase()));

    filtered.sort((a, b) => {
      switch (sortSelect.value) {
        case "updated_desc": return new Date(b.updated) - new Date(a.updated);
        case "updated_asc": return new Date(a.updated) - new Date(b.updated);
        case "name_desc": return b.title.localeCompare(a.title);
        default: return a.title.localeCompare(b.title);
      }
    });

    filtered.forEach((mod, i) => {
      const row = document.createElement("div");
      row.className = "px-3 py-2 text-sm rounded cursor-pointer flex justify-between items-center hover:bg-gray-700 transition transform opacity-0 -translate-x-4";
      row.innerHTML = `
        <span class="truncate">${highlightTerm(mod.title, searchInput.value)}</span>
        <div class="flex items-center gap-2">
          <span class="${mod.enabled ? 'text-green-400' : 'text-red-400'} text-xs">${mod.enabled ? "✔️" : "❌"}</span>
          <span class="${mod.favorite ? 'text-yellow-400' : 'text-gray-500'} text-xs">★</span>
        </div>
      `;
      row.onclick = () => {
        selectedMod = mod;
        renderDetail();
        highlightSelectedRow();
      };
      listEl.appendChild(row);
      rowElements.set(mod.id, row);
      setTimeout(() => row.classList.remove("opacity-0", "-translate-x-4"), i * 30);
    });

    highlightSelectedRow();
  }

  function highlightSelectedRow() {
    rowElements.forEach((row, id) => {
      row.classList.toggle("bg-gray-700", selectedMod && selectedMod.id === id);
    });
  }

  function renderDetail() {
    if (!selectedMod) return;
    const mod = selectedMod;
    detailEl.classList.remove("hidden");

    document.getElementById("detail-img").src = mod.preview;
    document.getElementById("detail-title").innerHTML = highlightTerm(mod.title, searchInput.value);
    document.getElementById("detail-desc").innerHTML = bbcodeToHtml(mod.description);
    document.getElementById("detail-meta").innerText = `ID: ${mod.id} • Updated: ${mod.updated}`;
    document.getElementById("detail-workshop").href = mod.workshop_url || "#";

    const toggleBtn = document.getElementById("detail-toggle");
    toggleBtn.innerText = mod.enabled ? "Turn Off" : "Turn On";
    toggleBtn.className = `px-3 py-1 rounded text-white ${mod.enabled ? "bg-red-600 hover:bg-red-500" : "bg-green-600 hover:bg-green-500"}`;
    toggleBtn.onclick = async () => {
      await fetch(`/api/mods/${mod.enabled ? 'disable' : 'enable'}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ id: mod.id, mod: mod.mod })
      });
      mod.enabled = !mod.enabled;
      renderList();
      renderDetail();
    };

    document.getElementById("detail-favorite").onclick = () => {
      mod.favorite = !mod.favorite;
      highlightSelectedRow();
      renderList();
    };

    document.getElementById("detail-hide").onclick = () => {
      mod.hidden = true;
      renderList();
      detailEl.classList.add("hidden");
    };

    document.getElementById("detail-download").onclick = () => {
      const a = document.createElement('a');
      a.href = mod.preview;
      a.download = `${mod.title || mod.id}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    };
  }

  exportEnabledBtn.onclick = () => {
    const enabledMods = mods.filter(m => m.enabled);
    const blob = new Blob([JSON.stringify(enabledMods, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'enabled-mods.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  [searchInput, filterSelect, sortSelect].forEach(el => el.addEventListener('input', renderList));

  renderList();
});
