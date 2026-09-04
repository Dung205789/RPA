import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\object2.png (input, score 0.82)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.CONTROL).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.72)
        // click 'Fit Page' (exact-visible)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_BOTTOM).keyUp(Keys.CONTROL).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.99)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\object15.png (a, score 0.76)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.99)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\object7.png (div, score 0.77)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.99)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.99)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        driver.switchTo().activeElement().sendKeys("Test");
        actions.doubleClick(cell).perform();   // element created in step 27
        actions.sendKeys("Login").perform();   // into element created in step 27
        actions.doubleClick(cell).perform();   // element created in step 32
        actions.sendKeys("Register").perform();   // into element created in step 32

        driver.quit();
    }
}