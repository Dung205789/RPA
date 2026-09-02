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

        driver.findElement(By.xpath("/html/body/div[10]/table/tbody/tr[5]/td[2]")).click();
        ArrayList<String> tab0 = new ArrayList<String>(driver.getWindowHandles());
        driver.switchTo().window(tab0.get(1));

        driver.quit();
    }
}