const katex = require('katex');

function tryRenderFull(raw) {
  const s = raw.trim();
  // Strip outer $ if present
  let clean = s;
  if (clean.startsWith('$') && clean.endsWith('$')) {
    clean = clean.slice(1, -1).trim();
  }
  // If it has internal stray $, remove them if it makes it valid
  if (clean.includes('$')) {
    const withoutDollars = clean.replace(/\$/g, '');
    try {
      return katex.renderToString(withoutDollars, { throwOnError: true });
    } catch {}
  }
  try {
    return katex.renderToString(clean, { throwOnError: true });
  } catch {
    return null;
  }
}

const opts = [
  "$\\pm 2$",
  "1 $\\pm 2i$",
  "$\\pm \\sqrt{2}$",
  "$\\pm i\\sqrt{3}$",
  "$C_1 e^x + C_2 e^{-x}$",
  "y = Ae^{2x} + Be^{-2x}",
  "y = A $\\cos 2x + B \\sin 2x$",
  "y = A $\\cos\\sqrt{2}x + B \\sin\\sqrt{2}x$",
  "y = A(x + B)e^{2x}",
  "Ae^t + Be^{-2t}",
  "e^{-2t}(A $\\cos t + B \\sin t$)",
  "e^t(A $\\cos 3t + B \\sin 3t$)",
  "Ae^t + Be^{3t}"
];

for (const o of opts) {
  const rendered = tryRenderFull(o);
  console.log(o, "->", rendered ? "FULL RENDER SUCCESS" : "NEEDS TOKENIZATION");
}
