import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click 'Style' (exact-visible)
        // click 'Sketch checkbox' (checkbox-label)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\diamond.png (a, score 0.96)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\rectangle.png (a, score 0.66)

        driver.quit();
    }
}