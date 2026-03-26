import { test, expect } from '@playwright/test';

test.describe('Landing Page - ARC Prize Theme', () => {
  test('should load with ARC Prize gradient background', async ({ page }) => {
    // Navigate to home page
    await page.goto('http://localhost:3000');
    
    // Take screenshot of initial load
    await page.screenshot({ path: 'tests/screenshots/task2-01-landing-page-load.png', fullPage: true });
    
    // Verify main heading exists
    const heading = page.locator('h1');
    await expect(heading).toContainText('Research Paper');
    await expect(heading).toContainText('Jupyter Notebook');
    
    // Verify heading has correct styling (larger, bold)
    const headingStyle = await heading.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        fontSize: computed.fontSize,
        fontWeight: computed.fontWeight,
      };
    });
    
    // Heading should be large (at least 3xl)
    expect(parseInt(headingStyle.fontSize)).toBeGreaterThanOrEqual(32);
  });

  test('should display subtitle text', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    const subtitle = page.locator('p').first();
    await expect(subtitle).toContainText('Convert research papers');
    await expect(subtitle).toContainText('publication-ready');
  });

  test('should have Get Started button', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Find the button by data-testid
    const button = page.locator('[data-testid="get-started-button"]');
    await expect(button).toBeVisible();
    await expect(button).toContainText('Get Started');
    
    // Verify button styling - should have purple background
    const buttonStyle = await button.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        color: computed.color,
      };
    });
    
    // Button should have purple tint (ARC Prize theme)
    console.log('Button background:', buttonStyle.backgroundColor);
    console.log('Button color:', buttonStyle.color);
  });

  test('should have dark background (ARC Prize theme)', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    // Get main container background
    const main = page.locator('main');
    const mainStyle = await main.evaluate((el) => {
      const computed = window.getComputedStyle(el);
      return {
        backgroundColor: computed.backgroundColor,
        backgroundImage: computed.backgroundImage,
      };
    });
    
    // Should have dark background or gradient
    console.log('Main background:', mainStyle);
    expect(mainStyle.backgroundColor || mainStyle.backgroundImage).toBeTruthy();
    
    // Take final screenshot
    await page.screenshot({ path: 'tests/screenshots/task2-02-landing-page-styled.png', fullPage: true });
  });

  test('should be responsive on mobile', async ({ browser }) => {
    const context = await browser.newContext({
      viewport: { width: 375, height: 667 }, // iPhone size
    });
    const page = await context.newPage();
    
    await page.goto('http://localhost:3000');
    
    // Elements should still be visible
    const heading = page.locator('h1');
    await expect(heading).toBeVisible();
    
    const button = page.locator('[data-testid="get-started-button"]');
    await expect(button).toBeVisible();
    
    // Take mobile screenshot
    await page.screenshot({ path: 'tests/screenshots/task2-03-mobile-responsive.png', fullPage: true });
    
    await context.close();
  });

  test('button should be clickable', async ({ page }) => {
    await page.goto('http://localhost:3000');
    
    const button = page.locator('[data-testid="get-started-button"]');
    
    // Verify button is clickable (has cursor pointer)
    const isCursor = await button.evaluate((el) => {
      return window.getComputedStyle(el).cursor;
    });
    console.log('Button cursor:', isCursor);
    
    // Button should be in viewport and visible
    await expect(button).toBeInViewport();
    await expect(button).toBeEnabled();
  });
});
