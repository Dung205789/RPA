import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[1]/div[1]/a[5]")).click();
        driver.findElement(By.xpath("/html/body/div[10]/table/tbody/tr[3]/td[2]")).click();
        driver.findElement(By.xpath("/html/body/div[11]/table/tbody/tr[3]/td[2]")).click();
        // click D:\SVG_Agent\documents\RPA_Datasets\images\drawio\ellipse.png (a, score 0.85)

        driver.quit();
    }
}