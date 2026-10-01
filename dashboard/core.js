(() => {
  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function renderInline(value) {
    return escapeHtml(value)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  }

  function renderMarkdown(markdown) {
    const lines = String(markdown || "").split(/\r?\n/);
    const output = [];
    let inCode = false;
    let inList = false;
    let codeLines = [];

    function closeList() {
      if (inList) {
        output.push("</ul>");
        inList = false;
      }
    }

    for (const line of lines) {
      if (line.startsWith("```")) {
        closeList();
        if (inCode) {
          output.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
          codeLines = [];
          inCode = false;
        } else {
          inCode = true;
        }
        continue;
      }

      if (inCode) {
        codeLines.push(line);
        continue;
      }

      const heading = line.match(/^(#{1,4})\s+(.+)$/);
      if (heading) {
        closeList();
        const level = Math.min(heading[1].length + 1, 4);
        output.push(`<h${level}>${renderInline(heading[2])}</h${level}>`);
        continue;
      }

      const listItem = line.match(/^\s*[-*]\s+(.+)$/);
      if (listItem) {
        if (!inList) {
          output.push("<ul>");
          inList = true;
        }
        const item = listItem[1];
        const className = item.startsWith("[ ]") ? ' class="check-list"' : "";
        output.push(`<li${className}>${renderInline(item.replace(/^\[ \]\s*/, ""))}</li>`);
        continue;
      }

      closeList();
      if (line.trim()) {
        output.push(`<p>${renderInline(line)}</p>`);
      }
    }

    closeList();
    if (inCode && codeLines.length) {
      output.push(`<pre><code>${escapeHtml(codeLines.join("\n"))}</code></pre>`);
    }
    return output.join("");
  }

  async function api(path, options, context) {
    const headers = {
      "Content-Type": "application/json",
      "X-Subject-Id": context.subjectId,
      "X-Studio-Mode": context.mode === "workshop" ? "workshop" : "course",
      ...(options.headers || {}),
    };
    const response = await fetch(path, {
      ...options,
      headers,
    });
    const payload = await response.json();
    if (!response.ok) {
      throw new Error(payload.error || `Request failed: ${response.status}`);
    }
    return payload;
  }

  window.StudioCore = Object.freeze({
    escapeHtml,
    renderInline,
    renderMarkdown,
    api,
  });
})();
