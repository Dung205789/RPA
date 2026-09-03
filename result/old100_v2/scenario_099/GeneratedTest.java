import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[3]/div[1]/a[39]/span[2]")).click();
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\o99.png (a, score 0.57)

        driver.quit();
    }
}