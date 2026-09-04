import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[3]/div[2]/button")).click();
        // click 'Clipart' (exact-visible)
        // click 'Apply' (exact-visible)
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\o100.png (img, score 0.70)

        driver.quit();
    }
}