import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click 'UML' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\o99.png (a, score 0.57)

        driver.quit();
    }
}