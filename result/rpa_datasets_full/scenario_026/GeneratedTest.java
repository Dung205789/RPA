import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/a[438]/span[2]")).click();

        driver.findElement(By.xpath("//body/div[3]/div[1]/div[4]/div[1]/a[3]")).click();

        driver.quit();
    }
}