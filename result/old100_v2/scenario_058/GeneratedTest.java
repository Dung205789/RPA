import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[4]/div[2]/div[1]/div[2]/div/div[3]/span")).click();
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\object23.png (img, score 0.79)
        driver.findElement(By.xpath("/html/body/div[3]/div[1]/a[4]/span[2]")).click();

        driver.quit();
    }
}