import { test, expect } from '@playwright/test'

const UPLOAD_URL = 'http://localhost:3000/upload'

test.describe('Session Management', () => {
  test('clear session button is hidden when no API key is set', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await expect(page.getByTestId('clear-session-button')).not.toBeVisible()
  })

  test('clear session button appears after entering an API key', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await page.getByTestId('api-key-input').fill('sk-mykey123')
    await expect(page.getByTestId('clear-session-button')).toBeVisible()
  })

  test('clear session button removes the key and hides itself', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await page.getByTestId('api-key-input').fill('sk-mykey123')
    await expect(page.getByTestId('clear-session-button')).toBeVisible()

    await page.getByTestId('clear-session-button').click()

    await expect(page.getByTestId('api-key-input')).toHaveValue('')
    await expect(page.getByTestId('clear-session-button')).not.toBeVisible()
  })

  test('session expiry is shown after entering an API key', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await page.getByTestId('api-key-input').fill('sk-testkey')
    await expect(page.getByTestId('session-expiry')).toBeVisible()
    await expect(page.getByTestId('session-expiry')).toContainText('Expires')
  })

  test('session expiry disappears after clear session', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await page.getByTestId('api-key-input').fill('sk-testkey')
    await expect(page.getByTestId('session-expiry')).toBeVisible()

    await page.getByTestId('clear-session-button').click()
    await expect(page.getByTestId('session-expiry')).not.toBeVisible()
  })

  test('API key is saved to sessionStorage with an expiry timestamp', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await page.getByTestId('api-key-input').fill('sk-timestamptest')

    const { key, expiry } = await page.evaluate(() => ({
      key: sessionStorage.getItem('openai_api_key'),
      expiry: sessionStorage.getItem('openai_api_key_expiry'),
    }))

    expect(key).toBe('sk-timestamptest')
    expect(expiry).not.toBeNull()
    expect(Number(expiry)).toBeGreaterThan(Date.now())
  })

  test('expiry is approximately 1 hour from now', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await page.getByTestId('api-key-input').fill('sk-expirytest')

    const expiry = await page.evaluate(() =>
      Number(sessionStorage.getItem('openai_api_key_expiry'))
    )

    const oneHourMs = 60 * 60 * 1000
    const diff = expiry - Date.now()
    expect(diff).toBeGreaterThan(oneHourMs - 5000) // within 5s tolerance
    expect(diff).toBeLessThanOrEqual(oneHourMs + 1000)
  })

  test('clear session removes all session keys', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    // Seed extra session keys
    await page.evaluate(() => {
      sessionStorage.setItem('openai_api_key', 'sk-test')
      sessionStorage.setItem('openai_api_key_expiry', String(Date.now() + 3600000))
      sessionStorage.setItem('extraction_result', JSON.stringify({ pages: [] }))
      sessionStorage.setItem('analysis_result', JSON.stringify({ abstract: 'x' }))
    })

    // Reload so the component picks up the key
    await page.reload()
    await page.getByTestId('clear-session-button').click()

    const remaining = await page.evaluate(() => ({
      apiKey: sessionStorage.getItem('openai_api_key'),
      expiry: sessionStorage.getItem('openai_api_key_expiry'),
      extraction: sessionStorage.getItem('extraction_result'),
      analysis: sessionStorage.getItem('analysis_result'),
    }))

    expect(remaining.apiKey).toBeNull()
    expect(remaining.expiry).toBeNull()
    expect(remaining.extraction).toBeNull()
    expect(remaining.analysis).toBeNull()
  })

  test('submit button is disabled after clear session', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await page.getByTestId('api-key-input').fill('sk-mykey')
    await page.getByTestId('clear-session-button').click()
    await expect(page.getByTestId('submit-button')).toBeDisabled()
  })

  test('restores API key from sessionStorage on page load', async ({ page }) => {
    // Seed session before navigating
    await page.goto(UPLOAD_URL)
    await page.evaluate(() => {
      sessionStorage.setItem('openai_api_key', 'sk-restored')
      sessionStorage.setItem('openai_api_key_expiry', String(Date.now() + 3600000))
    })
    await page.reload()

    const value = await page.getByTestId('api-key-input').inputValue()
    // Input type=password — value is set but masked; check sessionStorage
    expect(value).toBe('sk-restored')
    await expect(page.getByTestId('clear-session-button')).toBeVisible()
  })

  test('expired session is cleared on page load', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    // Inject an already-expired session
    await page.evaluate(() => {
      sessionStorage.setItem('openai_api_key', 'sk-expired')
      sessionStorage.setItem('openai_api_key_expiry', String(Date.now() - 1000))
    })
    await page.reload()

    await expect(page.getByTestId('api-key-input')).toHaveValue('')
    await expect(page.getByTestId('clear-session-button')).not.toBeVisible()
  })
})
