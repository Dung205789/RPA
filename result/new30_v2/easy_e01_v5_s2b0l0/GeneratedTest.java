import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\ellipse.png (a, score 1.00)
        // click D:\SVG_Agent\documents\RPA_drawio\shape_icons\ellipse.png (a, score 0.98)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_DOWN).keyUp(Keys.SHIFT).perform(); }
        actions.doubleClick(cell).perform();   // element created in step 2
        actions.sendKeys("Nightly timer fires").perform();   // into element created in step 2
        actions.doubleClick(cell).perform();   // element created in step 3
        actions.sendKeys("Backup complete").perform();   // into element created in step 3
        actions.clickAndHold(src).moveToElement(dst).release().perform();

        driver.quit();
    }
}