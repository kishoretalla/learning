import { test, expect } from '@playwright/test'

test.describe('Authentication Pages', () => {
  test('signup page loads and has required fields', async ({ page }) => {
    await page.goto('/signup')
    
    // Check page title
    await expect(page.locator ('h1')).toContainText('Create Account')
    
    // Check form fields exist
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[name="password"]')).toBeVisible()
    await expect(page.locator('text=Confirm Password')).toBeVisible()
    
    // Check submit button exists
    await expect(page.locator('button[type="submit"]')).toContainText('Create Account')
  })

  test('login page loads and has required fields', async ({ page }) => {
    await page.goto('/login')
    
    // Check page title
    await expect(page.locator('h1')).toContainText('Sign In')
    
    // Check form fields exist
    await expect(page.locator('input[type="email"]')).toBeVisible()
    await expect(page.locator('input[type="password"]')).toBeVisible()
    
    // Check submit button exists
    await expect(page.locator('button[type="submit"]')).toContainText('Sign In')
  })

  test('signup page has link to login', async ({ page }) => {
    await page.goto('/signup')
    
    const loginLink = page.locator('a:has-text("Sign in")')
    await expect(loginLink).toBeVisible()
    await expect(loginLink).toHaveAttribute('href', '/login')
  })

  test('login page has link to signup', async ({ page }) => {
    await page.goto('/login')
    
    const signupLink = page.locator('a:has-text("Create one")')
    await expect(signupLink).toBeVisible()
    await expect(signupLink).toHaveAttribute('href', '/signup')
  })

  test('signup validation shows error for empty fields', async ({ page }) => {
    await page.goto('/signup')
    
    // Try to submit empty form
    await page.locator('button[type="submit"]').click()
    
    // Should show validation error
    await expect(page.locator('text=Email is required')).toBeVisible()
  })

  test('signup validation shows error for short password', async ({ page }) => {
    await page.goto('/signup')
    
    // Fill in email and short password
    await page.locator('input[type="email"]').fill('test@example.com')
    await page.locator('input[placeholder="••••••••"]').first().fill('short')
    await page.locator('input[placeholder="••••••••"]').nth(1).fill('short')
    
    // Try to submit
    await page.locator('button[type="submit"]').click()
    
    // Should show validation error
    await expect(page.locator('text=Password must be at least 8 characters')).toBeVisible()
  })

  test('signup validation shows error when passwords do not match', async ({ page }) => {
    await page.goto('/signup')
    
    // Fill in form with mismatched passwords
    await page.locator('input[type="email"]').fill('test@example.com')
    await page.locator('input[placeholder="••••••••"]').first().fill('ValidPassword123')
    await page.locator('input[placeholder="••••••••"]').nth(1).fill('DifferentPassword123')
    
    // Try to submit
    await page.locator('button[type="submit"]').click()
    
    // Should show validation error
    await expect(page.locator('text=Passwords do not match')).toBeVisible()
  })

  test('login page shows error for empty credentials', async ({ page }) => {
    await page.goto('/login')
    
    // Try to submit empty form
    await page.locator('button[type="submit"]').click()
    
    // Should show validation error
    await expect(page.locator('text=Email and password are required')).toBeVisible()
  })

  test('both pages have back to home link', async ({ page }) => {
    // Check signup page
    await page.goto('/signup')
    const signupBackLink = page.locator('a:has-text("Back to home")')
    await expect(signupBackLink).toHaveAttribute('href', '/')
    
    // Check login page
    await page.goto('/login')
    const loginBackLink = page.locator('a:has-text("Back to home")')
    await expect(loginBackLink).toHaveAttribute('href', '/')
  })
})
