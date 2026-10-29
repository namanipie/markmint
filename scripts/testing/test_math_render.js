const katex = require('katex');

const expressions = [
  "\\pm 2",
  "1 \\pm 2i",
  "\\pm \\sqrt{2}",
  "\\pm i\\sqrt{3}",
  "D^2 - 2D + 1y = 0",
  "C_1 e^x + C_2 e^{-x}",
  "y = Ae^{2x} + Be^{-2x}",
  "A \\cos 2x + B \\sin 2x",
  "A \\cos\\sqrt{2}x + B \\sin\\sqrt{2}x",
  "y = A(x + B)e^{2x}",
  "(D^2 - 4)y = 0",
  "\\frac{d^2y}{dx^2} - 2\\frac{dy}{dx} + 2y = 0"
];

for (const expr of expressions) {
  try {
    const html = katex.renderToString(expr, { throwOnError: true });
    console.log(`OK: "${expr}" -> rendered length ${html.length}`);
  } catch (err) {
    console.error(`FAIL: "${expr}" -> ${err.message}`);
  }
}
