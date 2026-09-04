import org.openqa.selenium.*;
import org.openqa.selenium.interactions.Actions;

public class GeneratedTest {
    public static void main(String[] args) {
        WebDriver driver = new ChromeDriver();
        Actions actions = new Actions(driver);

        driver.get("https://app.diagrams.net/?lang=en&splash=0");
        driver.findElement(By.xpath("/html/body/div[4]/div[2]/div[1]/div[2]/div/div[3]/button")).click();
        driver.switchTo().activeElement().sendKeys("data:image/ jpeg ; <UNK> <UNK> <UNK> <UNK> AoHE9/Pzvj/APNj/wBmNarUfmS7jhX6Snz/AMy02FgMr2xhzGlxoGR4Y2+lnQKve0VjefJdyZIx15 pifl1 fWt3IxHqTgWx+t+sBzRnFdgG1WbzJPuC008 <UNK> <UNK> QLagp8bXtLXta9rhTmuAc1w6EHiomExMxO8OLb7bBds/FuLWZcNK/PhXj2R+lkBvRwPDwAK1mfH6O28dnacM1ldTh5 <UNK>");
        // click 'Apply' (exact-visible)

        driver.quit();
    }
}