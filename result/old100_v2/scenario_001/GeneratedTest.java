import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[1]/div[1]/a[1]")).click();
        driver.findElement(By.xpath("/html/body/div[10]/table/tbody/tr[16]/td[2]")).click();
        driver.findElement(By.xpath("/html/body/div[3]/div[1]/a[1]/div/img[3]")).click();

        driver.quit();
    }
}