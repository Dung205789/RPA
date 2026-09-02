import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//not-found")).click();

        driver.findElement(By.xpath("/html/body/div[6]/a/img")).click();
        ArrayList<String> tab0 = new ArrayList<String>(driver.getWindowHandles());
        driver.switchTo().window(tab0.get(1));

        driver.findElement(By.xpath("//not-found")).click();

        driver.findElement(By.xpath("//*[@id="repos-split-pane-content"]/div[1]/div[1]/div[1]/div[1]/div[1]/div[1]/div[3]/div[2]/div[1]/div[2]/article[1]/div[2]/h2[1]")).click();

        driver.quit();
    }
}