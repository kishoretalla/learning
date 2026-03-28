import { test, expect } from '@playwright/test'

const MOCK_ARXIV_RESPONSE = {
  filename: '1706.03762v7.pdf',
  title: 'Attention Is All You Need',
  source_url: 'https://arxiv.org/abs/1706.03762v7',
  total_pages: 1,
  total_chars: 180,
  pages: [
    {
      page_number: 1,
      text: 'Title: Attention Is All You Need\n\nAbstract: We propose the Transformer, a new network architecture based solely on attention mechanisms.',
      char_count: 128,
    },
  ],
  is_arxiv: true,
  analysis: {
    abstract: 'Transformer removes recurrence and relies on attention.',
    methodologies: ['self-attention', 'encoder-decoder'],
    algorithms: ['multi-head attention'],
    datasets: ['WMT 2014 English-German'],
    results: 'Improves BLEU while training faster.',
    conclusions: 'Attention-only architectures are effective.',
  },
}

async function seedAuthenticatedCookie(page: Parameters<typeof test>[1]['page']) {
  await page.context().addCookies([
    {
      name: 'session',
      value: 'playwright-e2e-session',
      domain: 'localhost',
      path: '/',
      httpOnly: false,
      secure: false,
      sameSite: 'Lax',
    },
  ])
}

test.describe('Full user flow', () => {
  test('user can enter API key, use arXiv URL, see processing state, and download notebook', async ({ page }) => {
    await seedAuthenticatedCookie(page)

    await page.route('**/api/arxiv-url', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(MOCK_ARXIV_RESPONSE),
      })
    })

    await page.route('**/api/export-markdown', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'text/markdown',
        headers: { 'content-disposition': 'attachment; filename="attention-is-all-you-need-notebook.md"' },
        body: '# Attention Is All You Need\n',
      })
    })

    await page.route('**/api/generate-notebook', async route => {
      await page.waitForTimeout(500)
      await route.fulfill({
        status: 200,
        contentType: 'application/octet-stream',
        headers: { 'content-disposition': 'attachment; filename="attention-is-all-you-need-notebook.ipynb"' },
        body: JSON.stringify({ cells: [], metadata: {}, nbformat: 4, nbformat_minor: 5 }),
      })
    })

    await page.route('**/api/create-colab-link', async route => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ available: false, reason: 'GITHUB_TOKEN not configured' }),
      })
    })

    await page.goto('http://localhost:3000/upload')
    await page.getByTestId('api-key-input').fill('AIza-playwright-test')
    await page.getByTestId('arxiv-url-input').fill('https://arxiv.org/abs/1706.03762')
    await page.screenshot({ path: 'tests/screenshots/full-flow-01-upload-ready.png' })

    await page.getByTestId('arxiv-submit-button').click()
    await page.waitForURL('**/processing')
    await expect(page.getByTestId('processing-title')).toBeVisible()
    await expect(page.getByTestId('step-analyze')).toContainText('Analyzing paper with Gemini')
    await page.screenshot({ path: 'tests/screenshots/full-flow-02-processing.png' })

    await expect(page.getByTestId('complete-title')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('download-button')).toBeVisible()
    await expect(page.getByTestId('markdown-download-button')).toBeVisible()
    await expect(page.getByTestId('colab-button').or(page.getByTestId('colab-unavailable'))).toBeVisible()
    await page.screenshot({ path: 'tests/screenshots/full-flow-03-success.png' })
  })
})