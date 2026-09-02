import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[7]/div[1]/a[10]")).click();

        driver.findElement(By.xpath("//not-found")).click();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("000000");

        driver.findElement(By.xpath("//not-found")).click();

        driver.quit();
    }
}