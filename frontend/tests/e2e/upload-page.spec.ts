import { test, expect } from '@playwright/test'
import path from 'path'
import fs from 'fs'

const UPLOAD_URL = 'http://localhost:3000/upload'

// Helper: create a minimal valid-ish PDF buffer for testing
function makePdfBuffer(sizeBytes = 1024): Buffer {
  const header = '%PDF-1.4\n'
  const footer = '\n%%EOF'
  const padding = 'x'.repeat(Math.max(0, sizeBytes - header.length - footer.length))
  return Buffer.from(header + padding + footer)
}

test.describe('Upload Page', () => {
  test('loads with correct heading and dark background', async ({ page }) => {
    await page.goto(UPLOAD_URL)
    await expect(page).toHaveURL(UPLOAD_URL)

    const title = page.getByTestId('page-title')
    await expect(title).toBeVisible()
    await expect(title).toContainText('Convert Your Paper')

    // Dark background
    const bg = await page.evaluate(() => {
      const el = document.querySelector('main')
      return el ? window.getComputedStyle(el).backgroundColor : ''
    })
    // Should not be white
    expect(bg).not.toBe('rgb(255, 255, 255)')

    await page.screenshot({ path: 'tests/screenshots/task3-01-upload-page-load.png' })
  })

  test('displays API key input and drop zone', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    await expect(page.getByTestId('api-key-input')).toBeVisible()
    await expect(page.getByTestId('drop-zone')).toBeVisible()
    await expect(page.getByTestId('submit-button')).toBeVisible()
  })

  test('submit button is disabled without API key and file', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    const btn = page.getByTestId('submit-button')
    await expect(btn).toBeDisabled()
  })

  test('submit button is disabled with only API key (no file)', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    await page.getByTestId('api-key-input').fill('sk-testkey123')
    const btn = page.getByTestId('submit-button')
    await expect(btn).toBeDisabled()
  })

  test('API key is persisted to sessionStorage', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    await page.getByTestId('api-key-input').fill('sk-mysessionkey')

    const stored = await page.evaluate(() => sessionStorage.getItem('openai_api_key'))
    expect(stored).toBe('sk-mysessionkey')
  })

  test('rejects non-PDF files with error message', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    // Upload a fake .txt file via the hidden input
    const txtPath = path.join('/tmp', 'test-upload.txt')
    fs.writeFileSync(txtPath, 'not a pdf')

    const fileInput = page.getByTestId('file-input')
    await fileInput.setInputFiles(txtPath)

    await expect(page.getByTestId('error-message')).toBeVisible()
    await expect(page.getByTestId('error-message')).toContainText('Only PDF files are supported')

    fs.unlinkSync(txtPath)
  })

  test('rejects PDF files over 10MB', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    // Create a file >10MB
    const bigPdfPath = path.join('/tmp', 'big-paper.pdf')
    const bigBuf = makePdfBuffer(11 * 1024 * 1024)
    fs.writeFileSync(bigPdfPath, bigBuf)

    const fileInput = page.getByTestId('file-input')
    await fileInput.setInputFiles(bigPdfPath)

    await expect(page.getByTestId('error-message')).toBeVisible()
    await expect(page.getByTestId('error-message')).toContainText('10MB limit')

    fs.unlinkSync(bigPdfPath)
  })

  test('accepts valid PDF and enables submit button', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    const pdfPath = path.join('/tmp', 'valid-paper.pdf')
    fs.writeFileSync(pdfPath, makePdfBuffer(512 * 1024)) // 512KB

    await page.getByTestId('api-key-input').fill('sk-testkey123')
    await page.getByTestId('file-input').setInputFiles(pdfPath)

    await expect(page.getByTestId('file-name')).toBeVisible()
    await expect(page.getByTestId('file-name')).toContainText('valid-paper.pdf')
    await expect(page.getByTestId('submit-button')).toBeEnabled()

    await page.screenshot({ path: 'tests/screenshots/task3-02-upload-ready.png' })

    fs.unlinkSync(pdfPath)
  })

  test('remove button clears selected file', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    const pdfPath = path.join('/tmp', 'remove-test.pdf')
    fs.writeFileSync(pdfPath, makePdfBuffer())

    await page.getByTestId('file-input').setInputFiles(pdfPath)
    await expect(page.getByTestId('file-name')).toBeVisible()

    await page.getByTestId('remove-file').click()
    await expect(page.getByTestId('file-name')).not.toBeVisible()

    fs.unlinkSync(pdfPath)
  })

  test('back link navigates to home', async ({ page }) => {
    await page.goto(UPLOAD_URL)

    await page.getByTestId('back-link').click()
    await expect(page).toHaveURL('http://localhost:3000/')
  })

  test('is responsive on mobile', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto(UPLOAD_URL)

    await expect(page.getByTestId('page-title')).toBeVisible()
    await expect(page.getByTestId('api-key-input')).toBeVisible()
    await expect(page.getByTestId('drop-zone')).toBeVisible()

    await page.screenshot({ path: 'tests/screenshots/task3-03-mobile-responsive.png' })
  })
})
