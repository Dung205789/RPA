import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\rectangle.png (a, score 0.57)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\rectangle.png (a, score 0.57)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\diamond.png (a, score 0.76)
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\trapezoid.png (a, score 0.62)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\rectangle.png (a, score 0.57)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\rectangle.png (a, score 0.57)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.doubleClick(cell).perform();   // element created in step 2
        actions.sendKeys("Lamp does not work").perform();   // into element created in step 2
        actions.doubleClick(cell).perform();   // element created in step 7
        actions.sendKeys("Check the socket").perform();   // into element created in step 7
        actions.doubleClick(cell).perform();   // element created in step 10
        actions.sendKeys("Plugged in ?").perform();   // into element created in step 10
        actions.doubleClick(cell).perform();   // element created in step 11
        actions.sendKeys("Plug it in").perform();   // into element created in step 11
        actions.doubleClick(cell).perform();   // element created in step 14
        actions.sendKeys("Replace the bulb").perform();   // into element created in step 14
        actions.doubleClick(cell).perform();   // element created in step 19
        actions.sendKeys("Lamp works").perform();   // into element created in step 19
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step10_to_step10
        actions.sendKeys("No").perform();   // into connector_from_step10_to_step10
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step10_to_step11
        actions.sendKeys("Yes").perform();   // into connector_from_step10_to_step11
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();

        driver.quit();
    }
}