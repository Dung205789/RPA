import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[2]/a")).click();

        driver.findElement(By.xpath("/html/body/div[4]/div[2]/div[3]/div[2]/div/select/option[11]")).click();

        driver.quit();
    }
}