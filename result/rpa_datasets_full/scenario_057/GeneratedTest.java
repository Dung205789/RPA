import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[4]/div[2]/div[1]/div[2]/div/div[3]/button")).click();

        WebElement textBox = driver.switchTo().activeElement();
        textBox.sendKeys("http://localhost:8123/uploads/stepImg/objectImg/objectImg__148__22__20251022.jpg");

        driver.findElement(By.xpath("//not-found")).click();

        driver.quit();
    }
}