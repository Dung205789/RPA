import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[4]/div[2]/div[3]/div[2]/div/select/option[1]")).click();
        driver.findElement(By.xpath("/html/body/div[4]/div[2]/div[3]/div[2]/div/select/option[9]")).click();

        driver.quit();
    }
}