import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\object2.png (input, score 0.82)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.72)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.99)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.SHIFT).perform(); }
        actions.clickAndHold(src).moveToElement(dst).release().perform();
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\65.png (input, score 0.99)
        // click 'Fit Page' (exact-visible)
        actions.doubleClick(cell).perform();   // element created in step 4
        actions.sendKeys("START").perform();   // into element created in step 4
        actions.doubleClick(cell).perform();   // element created in step 8
        actions.sendKeys("EXECUTE").perform();   // into element created in step 8
        actions.doubleClick(cell).perform();   // element created in step 12
        actions.sendKeys("END").perform();   // into element created in step 12
        actions.doubleClick(cell).perform();   // connector_from_step4_to_step8
        actions.sendKeys("begin").perform();   // into connector_from_step4_to_step8
        actions.doubleClick(cell).perform();   // connector_from_step8_to_step12
        actions.sendKeys("finish").perform();   // into connector_from_step8_to_step12

        driver.quit();
    }
}