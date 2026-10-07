// Render an HTML file to a Letter/A4 PDF via ego-browser's CDP (Page.printToPDF).
// usage: cd <engine folder>; write tracker/.pdf_jobs.json = [{"html": abs path, "pdf": abs path}];
//        then: ego-browser nodejs < scripts/html2pdf.mjs   (or set ENGINE_DIR=<engine folder>)
const fs = await import("node:fs/promises");
const root = process.env.ENGINE_DIR || process.cwd();
const cfgPath = root + "/tracker/.pdf_jobs.json";
const jobs = JSON.parse(await fs.readFile(cfgPath, "utf8"));
const task = await taskSpace(4);
let page = (await task.pages()).find(p => p.label === "p2") || await task.newPage();
await page.goto("about:blank");
const out = [];
for (const j of jobs) {
  const html = await fs.readFile(j.html, "utf8");
  await page.evaluate((h) => { document.open(); document.write(h); document.close(); }, html);
  await page.waitForTimeout(300);
  // auto-fit to one A4 page (11.69in at 96dpi) by stepping the font size down to 9pt at most
  const A4 = 11.69 * 96;
  const fit = await page.evaluate((A4) => {
    document.documentElement.style.width = "8.27in";
    document.body.style.width = "8.27in";
    document.body.style.margin = "0";
    for (let fs = 10; fs >= 9; fs -= 0.2) {
      document.body.style.setProperty("--fs", fs.toFixed(1) + "pt");
      if (document.body.getBoundingClientRect().height <= A4 - 6) return { fs: +fs.toFixed(1), ok: true };
    }
    return { fs: 9, ok: false };
  }, A4);
  const pages = fit.ok ? 1 : 2;
  const r = await page.cdp("Page.printToPDF", { paperWidth: 8.27, paperHeight: 11.69, marginTop: 0, marginBottom: 0, marginLeft: 0, marginRight: 0, printBackground: true, preferCSSPageSize: true });
  await fs.writeFile(j.pdf, Buffer.from(r.data, "base64"));
  out.push({ pdf: j.pdf.split('/').pop(), pages, fontPt: fit.fs });
}
console.log(JSON.stringify(out));
