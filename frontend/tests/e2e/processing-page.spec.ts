import { test, expect } from '@playwright/test'

const PROCESSING_URL = 'http://localhost:3000/processing'

const MOCK_EXTRACTION = {
  filename: 'arc-paper.pdf',
  total_pages: 2,
  total_chars: 500,
  pages: [
    { page_number: 1, text: 'This paper presents a novel GPT-4o approach.', char_count: 44 },
    { page_number: 2, text: 'Results show 85% accuracy on ARC benchmark.', char_count: 43 },
  ],
}

const MOCK_ANALYSIS = {
  abstract: 'A novel approach to ARC tasks using GPT-4o.',
  methodologies: ['few-shot prompting'],
  algorithms: ['beam search'],
  datasets: ['ARC-AGI'],
  results: 'Achieved 85% on ARC public eval.',
  conclusions: 'LLMs can solve abstract reasoning tasks.',
}

/** Inject session data so the page believes an upload already happened */
async function seedSession(page: Parameters<typeof test>[1]['page']) {
  await page.goto('http://localhost:3000/')
  await page.evaluate(
    ([extraction, apiKey]) => {
      sessionStorage.setItem('extraction_result', extraction)
      sessionStorage.setItem('openai_api_key', apiKey)
    },
    [JSON.stringify(MOCK_EXTRACTION), 'sk-test-key']
  )
}

test.describe('Processing Page', () => {
  test('shows no-data state when sessionStorage is empty', async ({ page }) => {
    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('no-data-state')).toBeVisible()
    await expect(page.getByText('No paper found')).toBeVisible()
    await page.screenshot({ path: 'tests/screenshots/task7-01-no-data.png' })
  })

  test('no-data state has link back to upload', async ({ page }) => {
    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('no-data-state').getByRole('link')).toBeVisible()
  })

  test('shows step list when session data exists (backend may be down)', async ({ page }) => {
    await seedSession(page)

    // Mock backend to avoid real API calls
    await page.route('**/api/analyze-paper', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYSIS) })
    )
    await page.route('**/api/generate-notebook', route => {
      const nb = JSON.stringify({ cells: [], metadata: {}, nbformat: 4, nbformat_minor: 5 })
      route.fulfill({
        status: 200,
        contentType: 'application/octet-stream',
        headers: { 'content-disposition': 'attachment; filename="arc-paper-notebook.ipynb"' },
        body: nb,
      })
    })

    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('step-list')).toBeVisible()
    await expect(page.getByTestId('step-extract')).toBeVisible()
    await expect(page.getByTestId('step-analyze')).toBeVisible()
    await expect(page.getByTestId('step-generate')).toBeVisible()
  })

  test('extract step is already marked done on load', async ({ page }) => {
    await seedSession(page)
    await page.route('**/api/analyze-paper', route => route.abort())
    await page.goto(PROCESSING_URL)
    const extractStep = page.getByTestId('step-extract')
    await expect(extractStep).toContainText('Text extracted from PDF')
    await expect(extractStep.getByText('✓')).toBeVisible()
  })

  test('reaches complete state and shows download button on success', async ({ page }) => {
    await seedSession(page)

    await page.route('**/api/analyze-paper', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYSIS) })
    )
    await page.route('**/api/generate-notebook', route => {
      const nb = JSON.stringify({ cells: [], metadata: {}, nbformat: 4, nbformat_minor: 5 })
      route.fulfill({
        status: 200,
        contentType: 'application/octet-stream',
        headers: { 'content-disposition': 'attachment; filename="arc-paper-notebook.ipynb"' },
        body: nb,
      })
    })
    // Colab link unavailable (no GITHUB_TOKEN in test env)
    await page.route('**/api/create-colab-link', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ available: false, reason: 'GITHUB_TOKEN not configured' }) })
    )

    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('complete-title')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('download-button')).toBeVisible()
    // Colab button shows either the ready button or the unavailable fallback
    await expect(
      page.getByTestId('colab-button').or(page.getByTestId('colab-unavailable'))
    ).toBeVisible({ timeout: 5000 })

    await page.screenshot({ path: 'tests/screenshots/task7-02-complete.png' })
  })

  test('download button has correct filename', async ({ page }) => {
    await seedSession(page)

    await page.route('**/api/analyze-paper', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYSIS) })
    )
    await page.route('**/api/generate-notebook', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/octet-stream',
        headers: { 'content-disposition': 'attachment; filename="arc-paper-notebook.ipynb"' },
        body: '{}',
      })
    })

    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('complete-title')).toBeVisible({ timeout: 10000 })
    const dl = page.getByTestId('download-button')
    await expect(dl).toHaveAttribute('download', /\.ipynb$/)
  })

  test('shows error state and retry button when analyze fails', async ({ page }) => {
    await seedSession(page)

    await page.route('**/api/analyze-paper', route =>
      route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ detail: 'Invalid OpenAI API key.' }) })
    )

    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('error-title')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('error-message')).toBeVisible()
    await expect(page.getByTestId('retry-button')).toBeVisible()

    await page.screenshot({ path: 'tests/screenshots/task7-03-error.png' })
  })

  test('shows error state when generate fails', async ({ page }) => {
    await seedSession(page)

    await page.route('**/api/analyze-paper', route =>
      route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify(MOCK_ANALYSIS) })
    )
    await page.route('**/api/generate-notebook', route =>
      route.fulfill({ status: 500, contentType: 'application/json', body: JSON.stringify({ detail: 'Generation failed.' }) })
    )

    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('error-title')).toBeVisible({ timeout: 10000 })
    await expect(page.getByTestId('retry-button')).toBeVisible()
  })

  test('error message contains API error detail', async ({ page }) => {
    await seedSession(page)

    await page.route('**/api/analyze-paper', route =>
      route.fulfill({ status: 429, contentType: 'application/json', body: JSON.stringify({ detail: 'OpenAI rate limit reached.' }) })
    )

    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('error-message')).toContainText('rate limit', { timeout: 10000 })
  })

  test('is responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto(PROCESSING_URL)
    await expect(page.getByTestId('no-data-state')).toBeVisible()
    await page.screenshot({ path: 'tests/screenshots/task7-04-mobile.png' })
  })
})
