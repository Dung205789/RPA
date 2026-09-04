import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\ellipse.png (a, score 0.67)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\rectangle.png (a, score 0.57)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\parallelogram.png (a, score 0.62)
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\hexagon.png (a, score 0.68)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\ellipse.png (a, score 0.67)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.doubleClick(cell).perform();   // element created in step 2
        actions.sendKeys("Model loaded").perform();   // into element created in step 2
        actions.doubleClick(cell).perform();   // element created in step 7
        actions.sendKeys("Slice the model").perform();   // into element created in step 7
        actions.doubleClick(cell).perform();   // element created in step 10
        actions.sendKeys("Read the model file").perform();   // into element created in step 10
        actions.doubleClick(cell).perform();   // element created in step 11
        actions.sendKeys("Heat the nozzle").perform();   // into element created in step 11
        actions.doubleClick(cell).perform();   // element created in step 14
        actions.sendKeys("Part finished").perform();   // into element created in step 14
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();

        driver.quit();
    }
}