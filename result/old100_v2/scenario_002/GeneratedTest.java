import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        // click 'File' (exact-visible)
        // click 'Save' (exact-visible)
        driver.findElement(By.xpath("/html/body/div[11]/div/div[2]/button[3]")).click();

        driver.quit();
    }
}