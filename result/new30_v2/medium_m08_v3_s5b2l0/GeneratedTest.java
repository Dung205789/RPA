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
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\diamond.png (a, score 0.76)
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\diamond.png (a, score 0.76)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\rectangle.png (a, score 0.57)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\rectangle.png (a, score 0.57)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.doubleClick(cell).perform();   // element created in step 2
        actions.sendKeys("Application filed").perform();   // into element created in step 2
        actions.doubleClick(cell).perform();   // element created in step 5
        actions.sendKeys("Documents complete ?").perform();   // into element created in step 5
        actions.doubleClick(cell).perform();   // element created in step 6
        actions.sendKeys("Score above cutoff ?").perform();   // into element created in step 6
        actions.doubleClick(cell).perform();   // element created in step 12
        actions.sendKeys("Check the identity").perform();   // into element created in step 12
        actions.doubleClick(cell).perform();   // element created in step 18
        actions.sendKeys("Case closed").perform();   // into element created in step 18
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step5_to_step6
        actions.sendKeys("Complete").perform();   // into connector_from_step5_to_step6
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step5_to_step18
        actions.sendKeys("Missing").perform();   // into connector_from_step5_to_step18
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step6_to_step12
        actions.sendKeys("Above").perform();   // into connector_from_step6_to_step12
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step6_to_step12
        actions.sendKeys("Below").perform();   // into connector_from_step6_to_step12

        driver.quit();
    }
}