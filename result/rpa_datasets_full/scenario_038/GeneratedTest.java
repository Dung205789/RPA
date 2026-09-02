import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;
import java.util.Set;
import java.util.ArrayList;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/");

        driver.findElement(By.xpath("//body/div[7]/div[1]/input[1]")).click();

        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[16]/td[2]")).click();

        driver.quit();
    }
}