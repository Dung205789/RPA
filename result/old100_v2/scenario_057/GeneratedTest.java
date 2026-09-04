import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[4]/div[2]/div[1]/div[2]/div/div[3]/button")).click();
        driver.switchTo().activeElement().sendKeys("http://localhost:8123/uploads/stepImg/objectImg/objectImg__148__22__20251022.jpg");
        // click 'Apply' (exact-visible)

        driver.quit();
    }
}