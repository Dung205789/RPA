import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\diamond.png (a, score 0.96)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_UP).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\diamond.png (a, score 0.96)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.doubleClick(cell).perform();   // element created in step 1
        actions.sendKeys("Lunch time").perform();   // into element created in step 1
        actions.doubleClick(cell).perform();   // element created in step 4
        actions.sendKeys("Hungry ?").perform();   // into element created in step 4
        actions.doubleClick(cell).perform();   // element created in step 6
        actions.sendKeys("Wait for 30 mins").perform();   // into element created in step 6
        actions.doubleClick(cell).perform();   // element created in step 9
        actions.sendKeys("Restaurant ?").perform();   // into element created in step 9
        actions.doubleClick(cell).perform();   // element created in step 10
        actions.sendKeys("Cook by your self").perform();   // into element created in step 10
        actions.doubleClick(cell).perform();   // element created in step 12
        actions.sendKeys("Full").perform();   // into element created in step 12
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step4_to_step6
        actions.sendKeys("No").perform();   // into connector_from_step4_to_step6
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step4_to_step9
        actions.sendKeys("Yes").perform();   // into connector_from_step4_to_step9
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step9_to_step10
        actions.sendKeys("No").perform();   // into connector_from_step9_to_step10
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.doubleClick(cell).perform();   // connector_from_step9_to_step12
        actions.sendKeys("Yes").perform();   // into connector_from_step9_to_step12
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        actions.clickAndHold(src).moveToElement(dst).release().perform();

        driver.quit();
    }
}