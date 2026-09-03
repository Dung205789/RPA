import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\object2.png (input, score 0.82)
        driver.findElement(By.xpath("/html/body/div[10]/table/tbody/tr[15]/td[2]")).click();
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\parallelogram.png (a, score 1.00)
        for (int i = 0; i < 15; i++) { actions.keyDown(Keys.SHIFT).sendKeys(Keys.ARROW_LEFT).keyUp(Keys.SHIFT).perform(); }

        driver.quit();
    }
}