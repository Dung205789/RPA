import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("/html/body/div[3]/div[1]/div[4]/div/a[5]")).click();

        WebElement object1 = driver.findElement(By.cssSelector(".geDiagramContainer svg > g > g:nth-child(2) > g:nth-child(23)"));
        actions.click(object1).perform();
        actions.sendKeys(Keys.DELETE).perform();

        driver.quit();
    }
}