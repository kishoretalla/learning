import { chromium } from '@playwright/test';
import fs from 'node:fs';
import path from 'node:path';

const apiKey = process.env.GEMINI_API_KEY;
if (!apiKey) {
  console.error('GEMINI_API_KEY is required.');
  process.exit(1);
}

const repoRoot = path.resolve(process.cwd(), '..');
const qualityDir = path.join(repoRoot, 'tests', 'quality');
const screenshotsDir = path.join(qualityDir, 'screenshots');

fs.mkdirSync(screenshotsDir, { recursive: true });

const outputNotebook = path.join(qualityDir, 'attention_output.ipynb');
const outputMarkdown = path.join(qualityDir, 'attention_output.md');

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ acceptDownloads: true });
const page = await context.newPage();

try {
  await context.addCookies([
    {
      name: 'session',
      value: 'real-quality-session',
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
    },
  ]);

  await page.goto('http://localhost:3000/upload', { waitUntil: 'domcontentloaded', timeout: 60000 });
  await page.getByTestId('page-title').waitFor({ state: 'visible', timeout: 60000 });

  const apiKeyInput = page.getByTestId('api-key-input');
  const arxivInput = page.getByTestId('arxiv-url-input');

  await apiKeyInput.click();
  await apiKeyInput.press('Meta+A');
  await apiKeyInput.press('Backspace');
  await apiKeyInput.type(apiKey, { delay: 15 });

  await arxivInput.click();
  await arxivInput.press('Meta+A');
  await arxivInput.press('Backspace');
  await arxivInput.type('https://arxiv.org/abs/1706.03762', { delay: 15 });
  await arxivInput.blur();
  const apiKeyVal = await page.getByTestId('api-key-input').inputValue();
  const arxivVal = await page.getByTestId('arxiv-url-input').inputValue();
  if (!apiKeyVal.trim() || !arxivVal.trim()) {
    await page.screenshot({ path: path.join(screenshotsDir, 'real-quality-debug-inputs-missing.png'), fullPage: true });
    throw new Error(`Input hydration mismatch: apiKey=${apiKeyVal.length}, arxiv=${arxivVal.length}`);
  }

  try {
    await page.waitForFunction(() => {
      const btn = document.querySelector('[data-testid="arxiv-submit-button"]');
      const api = document.querySelector('[data-testid="api-key-input"]');
      const arxiv = document.querySelector('[data-testid="arxiv-url-input"]');
      if (!btn || !api || !arxiv) return false;
      const apiVal = api.value || '';
      const arxivVal = arxiv.value || '';
      return apiVal.trim().length > 0 && arxivVal.trim().length > 0 && !btn.disabled;
    }, { timeout: 30000 });
  } catch (error) {
    const debug = await page.evaluate(() => {
      const btn = document.querySelector('[data-testid="arxiv-submit-button"]');
      const api = document.querySelector('[data-testid="api-key-input"]');
      const arxiv = document.querySelector('[data-testid="arxiv-url-input"]');
      return {
        href: location.href,
        apiValueLength: (api?.value || '').length,
        arxivValueLength: (arxiv?.value || '').length,
        buttonDisabled: btn ? !!btn.disabled : null,
        buttonText: btn?.textContent || null,
      };
    });
    await page.screenshot({ path: path.join(screenshotsDir, 'real-quality-debug-wait-timeout.png'), fullPage: true });
    throw new Error(`Enable-wait timeout. Debug=${JSON.stringify(debug)}; cause=${error}`);
  }

  const submitBtn = page.getByTestId('arxiv-submit-button');
  if (await submitBtn.isDisabled()) {
    await page.screenshot({ path: path.join(screenshotsDir, 'real-quality-debug-submit-disabled.png'), fullPage: true });
    throw new Error('arxiv-submit-button remained disabled after inputs were set.');
  }

  await page.screenshot({ path: path.join(screenshotsDir, 'real-quality-01-upload-ready.png'), fullPage: true });

  await submitBtn.click();
  await page.waitForURL('**/processing', { timeout: 60000 });
  await page.getByTestId('processing-title').waitFor({ state: 'visible', timeout: 60000 });
  await page.screenshot({ path: path.join(screenshotsDir, 'real-quality-02-processing.png'), fullPage: true });

  await page.getByTestId('complete-title').waitFor({ state: 'visible', timeout: 240000 });
  await page.getByTestId('download-button').waitFor({ state: 'visible', timeout: 60000 });
  await page.screenshot({ path: path.join(screenshotsDir, 'real-quality-03-success.png'), fullPage: true });

  const notebookDownloadPromise = page.waitForEvent('download');
  await page.getByTestId('download-button').click();
  const notebookDownload = await notebookDownloadPromise;
  await notebookDownload.saveAs(outputNotebook);

  const markdownButton = page.getByTestId('markdown-download-button');
  if (await markdownButton.isVisible()) {
    const markdownDownloadPromise = page.waitForEvent('download');
    await markdownButton.click();
    const markdownDownload = await markdownDownloadPromise;
    await markdownDownload.saveAs(outputMarkdown);
  }

  console.log(`Screenshots: ${screenshotsDir}`);
  console.log(`Notebook: ${outputNotebook}`);
  console.log(`Markdown: ${outputMarkdown}`);
} finally {
  await context.close();
  await browser.close();
}
