import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[1]/div[1]/a[6]")).click();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("a");

        driver.switchTo().activeElement().sendKeys(Keys.ENTER);

        driver.quit();
    }
}