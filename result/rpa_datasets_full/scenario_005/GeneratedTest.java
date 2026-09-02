import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[4]/div[3]/div/div[3]/div[5]")).click();

        driver.findElement(By.xpath("/html/body/div[7]/div[2]/a[1]")).click();

        driver.quit();
    }
}