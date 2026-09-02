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

        WebElement object5 = driver.findElement(By.xpath("//not-found"));
        object5.click();
        Thread.sleep(500);
        for(int i=0; i<30; i++) { actions.keyDown(Keys.CONTROL).sendKeys(Keys.ARROW_RIGHT).keyUp(Keys.CONTROL).perform(); }

        driver.quit();
    }
}