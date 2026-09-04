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
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\object2.png (input, score 0.82)
        // click 'Fit Page' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)
        actions.clickAndHold(src).moveToElement(dst).release().perform();

        driver.quit();
    }
}